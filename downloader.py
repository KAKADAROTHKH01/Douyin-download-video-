import os
import uuid
import yt_dlp


DOWNLOAD_DIR = "/tmp"


def download_video(url: str) -> str:
    video_id = uuid.uuid4().hex
    output = os.path.join(
        DOWNLOAD_DIR,
        f"{video_id}.%(ext)s"
    )

    options = {
        "outtmpl": output,
        "noplaylist": True,

        # Try MP4 first
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",

        "merge_output_format": "mp4",

        "quiet": False,
        "no_warnings": False,

        # Avoid using login cookies
        "cookiefile": None,

        # Useful for some sites
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 10; K) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/120.0 Mobile Safari/537.36"
            )
        },
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # yt-dlp may produce .mp4 after merging
        if os.path.exists(filename):
            return filename

        base, _ = os.path.splitext(filename)

        for ext in (".mp4", ".webm", ".mkv"):
            candidate = base + ext
            if os.path.exists(candidate):
                return candidate

        raise FileNotFoundError(
            "Video file was not created."
        )

    except Exception as e:
        raise RuntimeError(
            f"Downloader error: {str(e)}"
        ) from e
