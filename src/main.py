import traceback
from datetime import timedelta
from typing import Any

import httpx
from loguru import logger


class TwitchClientError(Exception): ...


class TwitchClient:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={"Client-ID": "kd1unb4b3q4t58fwlpcbzcbnm76a8fp"},
        )

    async def gql_request(self, query: str) -> Any:
        res = await self.client.post("https://gql.twitch.tv/gql", json={"query": query})
        if res.is_error:
            raise TwitchClientError(f"Error during request: {res.read()}")
        return res.json()

    def get_video_comments_by_offset_or_cursor(
        self, offset: timedelta | None = None, cursor: str | None = None
    ) -> None:
        pass


def main() -> None:
    pass


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Exiting...")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
