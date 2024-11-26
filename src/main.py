import traceback
from datetime import timedelta
from typing import Any

import httpx
from loguru import logger

VIDEO_ID = 2311425848


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
    ) -> tuple[Any, bool]:
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
        comments = res["data"]["video"]["comments"]
        return comments, comments["pageInfo"]["hasNextPage"]

    async def get_video(self) -> dict[str, Any]:
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
        video = await self.do_request(body={"query": gql_request})
        return video["data"]["video"]


def main() -> None:
    pass


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Exiting...")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
