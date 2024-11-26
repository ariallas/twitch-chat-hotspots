from datetime import timedelta

import pytest
from loguru import logger

from src.main import TwitchClient, get_comments, get_segment_comments


@pytest.fixture
def twitch_client() -> TwitchClient:
    return TwitchClient()


async def test_get_video(twitch_client: TwitchClient) -> None:
    res = await twitch_client.get_video()
    logger.info(res)


async def test_get_video_comments(twitch_client: TwitchClient) -> None:
    res = await twitch_client.get_video_comments(offset=timedelta(seconds=0))
    logger.info(res)


async def test_get_segment_comments(twitch_client: TwitchClient) -> None:
    comments = await get_segment_comments(
        twitch_client,
        start=timedelta(seconds=0),
        end=timedelta(hours=1),
    )
    logger.info(comments)


async def test_get_comments(twitch_client: TwitchClient) -> None:
    video = await twitch_client.get_video()
    comments = await get_comments(twitch_client, video)
    logger.info(comments)
