from datetime import timedelta

import pytest
from loguru import logger

from src.main import TwitchClient


@pytest.fixture
def twitch_client() -> TwitchClient:
    return TwitchClient()


async def test_get_video(twitch_client: TwitchClient) -> None:
    res = await twitch_client.get_video()
    logger.info(res)


async def test_get_video_comments(twitch_client: TwitchClient) -> None:
    res = await twitch_client.get_video_comments(offset=timedelta(seconds=0))
    logger.info(res)
