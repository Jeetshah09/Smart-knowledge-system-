"""YouTube resource support.

Uses the `youtube-transcript-api` package to fetch captions (the plain
timedtext endpoint no longer returns data for unauthenticated requests).
If no transcript is available the resource is still created, but we are
honest about the processing status.
"""
import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

WATCH_PATTERNS = (
    re.compile(r"(?:youtube\.com/watch\?.*v=)([\w-]{11})"),
    re.compile(r"(?:youtu\.be/)([\w-]{11})"),
    re.compile(r"(?:youtube\.com/embed/)([\w-]{11})"),
    re.compile(r"(?:youtube\.com/shorts/)([\w-]{11})"),
)


def extract_video_id(url: str) -> str | None:
    for pattern in WATCH_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    return None


def is_valid_youtube_url(url: str) -> bool:
    return extract_video_id(url) is not None


def extract_transcript(video_id: str) -> str | None:
    """Fetch a transcript for the video. Returns None when none is available."""
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["en", "hi"])
        return " ".join(segment.text for segment in fetched) or None
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable):
        # Expected cases - the video simply has no usable captions.
        return None
    except Exception:
        # Network hiccups, unexpected API changes, etc.
        return None
