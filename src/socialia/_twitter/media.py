"""Twitter media upload functionality (images and videos)."""

import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from requests_oauthlib import OAuth1Session

# Media type mappings
MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
}

# Video extensions that require chunked upload
VIDEO_EXTENSIONS = {".mp4", ".mov"}

MEDIA_UPLOAD_ENDPOINT = "https://upload.twitter.com/1.1/media/upload.json"


def upload_media(oauth: "OAuth1Session", file_path: str) -> dict:
    """
    Upload media file to Twitter (auto-detects image vs video).

    Args:
        oauth: Authenticated OAuth1Session
        file_path: Path to media file (jpg, png, gif, webp, mp4, mov)

    Returns:
        dict with 'success', 'media_id' or 'error'
    """
    path = Path(file_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    ext = path.suffix.lower()
    if ext not in MEDIA_TYPES:
        return {
            "success": False,
            "error": f"Unsupported file type: {ext}. Supported: {list(MEDIA_TYPES.keys())}",
        }

    # Route videos to chunked upload
    if ext in VIDEO_EXTENSIONS:
        return upload_video(oauth, file_path)

    # Simple upload for images
    with open(path, "rb") as f:
        media_data = f.read()

    files = {"media": media_data}
    response = oauth.post(MEDIA_UPLOAD_ENDPOINT, files=files)

    if response.status_code == 200:
        data = response.json()
        return {
            "success": True,
            "media_id": data["media_id_string"],
        }
    return {
        "success": False,
        "error": f"{response.status_code}: {response.text}",
    }


def upload_video(
    oauth: "OAuth1Session", file_path: str, chunk_size: int = 4 * 1024 * 1024
) -> dict:
    """
    Upload video to Twitter using chunked upload API.

    Twitter requires INIT -> APPEND (chunks) -> FINALIZE -> STATUS flow.

    Args:
        oauth: Authenticated OAuth1Session
        file_path: Path to video file (mp4, mov)
        chunk_size: Upload chunk size in bytes (default 4MB, max 5MB)

    Returns:
        dict with 'success', 'media_id' or 'error'
    """
    path = Path(file_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    ext = path.suffix.lower()
    media_type = MEDIA_TYPES.get(ext, "video/mp4")
    total_bytes = path.stat().st_size

    # Step 1: INIT
    init_params = {
        "command": "INIT",
        "total_bytes": total_bytes,
        "media_type": media_type,
        "media_category": "tweet_video",
    }
    response = oauth.post(MEDIA_UPLOAD_ENDPOINT, data=init_params)

    if response.status_code not in (200, 201, 202):
        return {
            "success": False,
            "error": f"INIT failed: {response.status_code}: {response.text}",
        }

    media_id = response.json()["media_id_string"]

    # Step 2: APPEND (chunked upload)
    with open(path, "rb") as f:
        segment_index = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            append_params = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": segment_index,
            }
            files = {"media": chunk}
            response = oauth.post(
                MEDIA_UPLOAD_ENDPOINT, data=append_params, files=files
            )

            if response.status_code not in (200, 201, 202, 204):
                return {
                    "success": False,
                    "error": f"APPEND segment {segment_index} failed: {response.status_code}: {response.text}",
                }

            segment_index += 1

    # Step 3: FINALIZE
    finalize_params = {
        "command": "FINALIZE",
        "media_id": media_id,
    }
    response = oauth.post(MEDIA_UPLOAD_ENDPOINT, data=finalize_params)

    if response.status_code not in (200, 201, 202):
        return {
            "success": False,
            "error": f"FINALIZE failed: {response.status_code}: {response.text}",
        }

    result = response.json()

    # Step 4: STATUS - Poll for processing completion (videos require transcoding)
    processing_info = result.get("processing_info")
    if processing_info:
        state = processing_info.get("state")
        check_after_secs = processing_info.get("check_after_secs", 5)

        while state in ("pending", "in_progress"):
            time.sleep(check_after_secs)

            status_params = {
                "command": "STATUS",
                "media_id": media_id,
            }
            response = oauth.get(MEDIA_UPLOAD_ENDPOINT, params=status_params)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"STATUS check failed: {response.status_code}: {response.text}",
                }

            result = response.json()
            processing_info = result.get("processing_info", {})
            state = processing_info.get("state")
            check_after_secs = processing_info.get("check_after_secs", 5)

            if state == "failed":
                error_info = processing_info.get("error", {})
                return {
                    "success": False,
                    "error": f"Video processing failed: {error_info.get('message', 'Unknown error')}",
                }

    return {
        "success": True,
        "media_id": media_id,
    }
