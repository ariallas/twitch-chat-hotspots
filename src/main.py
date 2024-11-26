from __future__ import annotations

import asyncio
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel, TypeAdapter
from tqdm.asyncio import tqdm_asyncio

# ruff: noqa: N815

VIDEO_ID = 2310845232
# VIDEO_ID = 2311425848
MAX_CONCURRENT = 20


async def main() -> None:
    twitch_client = TwitchClient()
    video = await twitch_client.get_video()
    comments = await get_comments_cached(twitch_client, video)
    logger.info(f"Got {len(comments)} comments")


async def get_comments_cached(twitch_client: TwitchClient, video: VideoInfo) -> list[CommentEdge]:
    file = Path("__cache") / f"{VIDEO_ID}.json"
    file.parent.mkdir(exist_ok=True)

    type_adapter = TypeAdapter(list[CommentEdge])
    if file.exists():
        return type_adapter.validate_json(file.read_bytes())

    comments = await get_comments(twitch_client, video)
    file.write_bytes(type_adapter.dump_json(comments))

    return comments


async def get_comments(twitch_client: TwitchClient, video: VideoInfo) -> list[CommentEdge]:
    step_seconds = 60
    tasks = [
        get_segment_comments(
            twitch_client,
            start=timedelta(seconds=start),
            end=timedelta(seconds=start + step_seconds),
        )
        for start in range(0, int(video.lengthSeconds.total_seconds()), step_seconds)
    ]
    comment_lists = await tqdm_asyncio.gather(*tasks)
    return [c for comment_list in comment_lists for c in comment_list]


semaphore = asyncio.Semaphore(MAX_CONCURRENT)


async def get_segment_comments(
    twitch_client: TwitchClient, start: timedelta, end: timedelta
) -> list[CommentEdge]:
    async with semaphore:
        segment_comments: list[CommentEdge] = []

        comments = await twitch_client.get_video_comments(offset=start)

        while True:
            if not comments.edges:
                break

            for edge in comments.edges:
                offset = edge.node.contentOffsetSeconds
                if start <= offset < end:
                    segment_comments.append(edge)
                if offset >= end:
                    break

            last_edge = comments.edges[-1]
            if last_edge.node.contentOffsetSeconds > end or not comments.pageInfo.hasNextPage:
                break

            comments = await twitch_client.get_video_comments(cursor=last_edge.cursor)

        return segment_comments


class TwitchClientError(Exception): ...


class TwitchClient:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={"Client-ID": "kd1unb4b3q4t58fwlpcbzcbnm76a8fp"},
        )

    async def do_request(self, body: dict[str, Any]) -> Any:
        res = await self.client.post("https://gql.twitch.tv/gql", json=body)
        if res.is_error:
            raise TwitchClientError(f"Error during request: {res.read()}")
        return res.json()

    async def get_video_comments(
        self, offset: timedelta | None = None, cursor: str | None = None
    ) -> Comments:
        """
        https://github.com/lay295/TwitchDownloader/blob/master/TwitchDownloaderCore/ChatDownloader.cs -> DownloadSection
        """
        assert offset is not None or cursor is not None

        search_parameter = (
            {"contentOffsetSeconds": int(offset.total_seconds())} if offset else {"cursor": cursor}
        )
        request_body = {
            "operationName": "VideoCommentsByOffsetOrCursor",
            "variables": {
                "videoID": str(VIDEO_ID),
            }
            | search_parameter,
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "b70a3591ff0f4e0313d126c6a1502d79a1c02baebb288227c582044aa76adf6a",
                }
            },
        }
        res = await self.do_request(request_body)
        return Comments.model_validate(res["data"]["video"]["comments"])

    async def get_video(self) -> VideoInfo:
        """
        https://github.com/lay295/TwitchDownloader/blob/master/TwitchDownloaderCore/TwitchHelper.cs -> GetVideoInfo
        """
        gql_request = f"""
            query {{
                video(id: "{VIDEO_ID}") {{
                    creator {{
                        displayName
                        id
                    }}
                    createdAt
                    lengthSeconds
                    title
                }}
            }}
        """
        resp = await self.do_request(body={"query": gql_request})
        logger.info(f"Got video: {resp}")
        return VideoInfo.model_validate(resp["data"]["video"])


###


class VideoInfo(BaseModel):
    createdAt: datetime
    lengthSeconds: timedelta
    title: str


###


class Comments(BaseModel):
    edges: list[CommentEdge]
    pageInfo: PageInfo


class CommentEdge(BaseModel):
    cursor: str
    node: CommentNode


class CommentNode(BaseModel):
    contentOffsetSeconds: timedelta
    createdAt: datetime


class PageInfo(BaseModel):
    hasNextPage: bool


###


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Exiting...")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
