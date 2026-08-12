import os
import re
import glob
import uuid
import logging
from urllib.parse import urlparse

import yt_dlp


# =========================================================
# CONFIG
# =========================================================

DOWNLOAD_DIR = "/tmp/douyin_downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


# =========================================================
# URL VALIDATION
# =========================================================

DOUYIN_HOSTS = {
    "douyin.com",
    "www.douyin.com",
    "iesdouyin.com",
    "www.iesdouyin.com",
    "v.douyin.com",
}


def is_douyin_url(url: str) -> bool:
    """
    Check whether URL belongs to Douyin.
    """

    try:
        parsed = urlparse(url)

        host = (parsed.netloc or "").lower()

        if ":" in host:
            host = host.split(":", 1)[0]

        return (
            host in DOUYIN_HOSTS
            or host.endswith(".douyin.com")
        )

    except Exception:
        return False


# =========================================================
# EXTRACT VIDEO ID
# =========================================================

def extract_video_id(url: str):
    """
    Extract video ID from URLs such as:

    https://www.iesdouyin.com/share/video/7618379465865179314/...
    https://www.douyin.com/video/7618379465865179314
    https://www.douyin.com/share/video/7618379465865179314
    """

    patterns = [
        r"/share/video/(\d+)",
        r"/video/(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


# =========================================================
# NORMALIZE DOUYIN URL
# =========================================================

def normalize_douyin_url(url: str):
    """
    Convert supported share URLs into a normal Douyin video URL.

    Example:

    iesdouyin.com/share/video/123456789
             ↓
    douyin.com/video/123456789
    """

    url = url.strip()

    video_id = extract_video_id(url)

    if video_id:
        normalized = (
            f"https://www.douyin.com/video/{video_id}"
        )

        logger.info(
            "Douyin URL normalized: %s -> %s",
            url[:100],
            normalized,
        )

        return normalized

    return url


# =========================================================
# CLEAN OLD FILES
# =========================================================

def cleanup_job_files(job_id: str):
    """
    Remove files created by this download job.
    """

    pattern = os.path.join(
        DOWNLOAD_DIR,
        f"{job_id}.*"
    )

    for file_path in glob.glob(pattern):
        try:
            os.remove(file_path)

        except OSError:
            pass


# =========================================================
# FIND DOWNLOADED FILE
# =========================================================

def find_downloaded_file(job_id: str):
    """
    Find the final downloaded media file.
    """

    pattern = os.path.join(
        DOWNLOAD_DIR,
        f"{job_id}.*"
    )

    files = glob.glob(pattern)

    # Ignore temporary files
    files = [
        path
        for path in files
        if not path.endswith(".part")
        and not path.endswith(".ytdl")
    ]

    if not files:
        return None

    # Prefer MP4
    mp4_files = [
        path
        for path in files
        if path.lower().endswith(".mp4")
    ]

    if mp4_files:
        return mp4_files[0]

    # Otherwise return first media file
    return files[0]


# =========================================================
# DOWNLOAD
# =========================================================

def download_douyin(url: str):
    """
    Download a public Douyin video.

    Returns:

        (file_path, title)

    or:

        None

    """

    if not url:
        logger.error("Empty URL")
        return None

    url = url.strip()

    # -----------------------------------------------------
    # Validate URL
    # -----------------------------------------------------

    if not is_douyin_url(url):
        logger.error("Not a Douyin URL: %s", url)
        return None

    # -----------------------------------------------------
    # Normalize share URL
    # -----------------------------------------------------

    normalized_url = normalize_douyin_url(url)

    video_id = extract_video_id(normalized_url)

    if not video_id:
        logger.error(
            "Unable to extract Douyin video ID: %s",
            url,
        )

        return None

    # -----------------------------------------------------
    # Job ID
    # -----------------------------------------------------

    job_id = uuid.uuid4().hex

    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{job_id}.%(ext)s",
    )

    # -----------------------------------------------------
    # yt-dlp options
    # -----------------------------------------------------

    ydl_opts = {
        "outtmpl": output_template,

        # Prefer MP4-compatible video/audio
        "format": (
            "bv*[ext=mp4]+ba[ext=m4a]/"
            "bv*+ba/"
            "b[ext=mp4]/"
            "b"
        ),

        "merge_output_format": "mp4",

        "noplaylist": True,

        # Network
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,

        # Do not download extra files
        "writethumbnail": False,
        "writeinfojson": False,
        "writesubtitles": False,
        "writeautomaticsub": False,

        # Cleaner filenames
        "restrictfilenames": True,

        # Logging
        "quiet": False,
        "no_warnings": False,

        # Avoid partial leftovers
        "continuedl": True,
        "nopart": False,

        # HTTP headers
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 10; K) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            "Referer": "https://www.douyin.com/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    }

    try:

        logger.info(
            "Starting Douyin download: %s",
            normalized_url,
        )

        # -------------------------------------------------
        # Extract + Download
        # -------------------------------------------------

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                normalized_url,
                download=True,
            )

            if not info:
                logger.error(
                    "yt-dlp returned no information"
                )

                cleanup_job_files(job_id)
                return None

            title = (
                info.get("title")
                or "Douyin Video"
            )

            logger.info(
                "Video title: %s",
                title,
            )

        # -------------------------------------------------
        # Find downloaded file
        # -------------------------------------------------

        file_path = find_downloaded_file(job_id)

        if not file_path:

            logger.error(
                "Download completed but file "
                "was not found"
            )

            cleanup_job_files(job_id)
            return None

        # -------------------------------------------------
        # Check file size
        # -------------------------------------------------

        try:
            file_size = os.path.getsize(file_path)

            logger.info(
                "Downloaded file: %s",
                file_path,
            )

            logger.info(
                "File size: %.2f MB",
                file_size / (1024 * 1024),
            )

        except OSError:
            pass

        return file_path, title

    except yt_dlp.utils.DownloadError as e:

        error_text = str(e)

        logger.error(
            "yt-dlp DownloadError: %s",
            error_text,
        )

        # -------------------------------------------------
        # Useful error detection
        # -------------------------------------------------

        if "Fresh cookies" in error_text:
            logger.error(
                "Douyin requires a fresh browser session/cookies."
            )

        elif "Unsupported URL" in error_text:
            logger.error(
                "Douyin URL is not supported by "
                "the current yt-dlp extractor."
            )

        elif "HTTP Error 403" in error_text:
            logger.error(
                "Douyin returned HTTP 403."
            )

        elif "HTTP Error 429" in error_text:
            logger.error(
                "Douyin returned HTTP 429 / rate limited."
            )

        elif "Unable to extract" in error_text:
            logger.error(
                "Douyin extractor could not extract "
                "the video information."
            )

        cleanup_job_files(job_id)

        return None

    except Exception as e:

        logger.exception(
            "Unexpected Douyin download error: %s",
            e,
        )

        cleanup_job_files(job_id)

        return None
