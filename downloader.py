import os
import uuid
import requests

DOWNLOAD_DIR = "/tmp"

TIKWM_API = "https://www.tikwm.com/api/"


def download_video(url: str) -> str:
    video_id = uuid.uuid4().hex
    output = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 10; K) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0 Mobile Safari/537.36"
        )
    }

    try:
        response = requests.post(
            TIKWM_API,
            data={"url": url, "hd": 1},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("code") != 0:
            raise RuntimeError(
                f"tikwm API error: {result.get('msg', 'unknown error')}"
            )

        data = result.get("data", {})
        # Prefer no-watermark HD play url, fallback to regular play url
        video_url = data.get("hdplay") or data.get("play")

        if not video_url:
            raise RuntimeError("No video URL returned from tikwm API")

        video_response = requests.get(video_url, headers=headers, timeout=60)
        video_response.raise_for_status()

        with open(output, "wb") as f:
            f.write(video_response.content)

        if os.path.exists(output):
            return output

        raise FileNotFoundError("Video file was not created.")

    except Exception as e:
        raise RuntimeError(f"Downloader error: {str(e)}") from e
