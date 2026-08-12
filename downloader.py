import os
import glob
import uuid
import yt_dlp


DOWNLOAD_DIR = "/tmp/douyin_downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_douyin(url: str):
    job_id = uuid.uuid4().hex

    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{job_id}.%(ext)s"
    )

    ydl_opts = {
        "outtmpl": output_template,

        # Best video + audio when available
        "format": "bv*+ba/b",

        # Merge into MP4 when possible
        "merge_output_format": "mp4",

        "noplaylist": True,

        "quiet": True,
        "no_warnings": True,

        "retries": 3,
        "fragment_retries": 3,

        "socket_timeout": 30,

        "restrictfilenames": True,

        # Avoid downloading extra files
        "writethumbnail": False,
        "writeinfojson": False,
        "writesubtitles": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            title = info.get("title") or "Douyin Video"

            # Find generated file
            files = glob.glob(
                os.path.join(
                    DOWNLOAD_DIR,
                    f"{job_id}.*"
                )
            )

            files = [
                f for f in files
                if not f.endswith(".part")
            ]

            if not files:
                return None

            # Prefer mp4
            mp4_files = [
                f for f in files
                if f.lower().endswith(".mp4")
            ]

            file_path = (
                mp4_files[0]
                if mp4_files
                else files[0]
            )

            return file_path, title

    except Exception:
        return None
