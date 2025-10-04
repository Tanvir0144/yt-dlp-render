from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import FileResponse
import yt_dlp
import os, base64, tempfile, time

app = FastAPI(title="YT-DLP Ultra Fast API", version="3.0")

# ---------------------------------------------------
# Global Config
# ---------------------------------------------------
CACHE_LIMIT = 50         # সর্বোচ্চ ৫০টা ভিডিও cache থাকবে
CACHE_TTL = 300          # ৫ মিনিট পর্যন্ত cache valid (in seconds)
stream_cache = {}        # {url: {"data": {...}, "time": timestamp}}

# ---------------------------------------------------
# yt-dlp options (optimized for Render)
# ---------------------------------------------------
def get_ydl_opts(extra_opts=None):
    opts = {
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "cachedir": False,
        "retries": 3,
        "ignoreerrors": True,
        "source_address": "0.0.0.0",
        "extractor_retries": 2,
    }
    # ✅ Cookie decode (optional)
    cookies_b64 = os.getenv("COOKIES_B64")
    if cookies_b64:
        try:
            cookies_data = base64.b64decode(cookies_b64).decode("utf-8")
            with open("cookies.txt", "w", encoding="utf-8") as f:
                f.write(cookies_data)
            opts["cookiefile"] = "cookies.txt"
        except Exception as e:
            print("⚠️ Cookie decode error:", e)
    if extra_opts:
        opts.update(extra_opts)
    return opts


# ---------------------------------------------------
# Cache Management System
# ---------------------------------------------------
def cleanup_cache():
    """Auto remove old/expired cache items"""
    now = time.time()
    expired = [url for url, v in stream_cache.items() if now - v["time"] > CACHE_TTL]
    for url in expired:
        stream_cache.pop(url, None)

    # যদি ৫০টার বেশি cache হয়, পুরনো গুলো ডিলিট করে দাও
    if len(stream_cache) > CACHE_LIMIT:
        sorted_items = sorted(stream_cache.items(), key=lambda x: x[1]["time"])
        for url, _ in sorted_items[:len(stream_cache) - CACHE_LIMIT]:
            stream_cache.pop(url, None)


# ---------------------------------------------------
# Root Route
# ---------------------------------------------------
@app.get("/")
def home():
    return {
        "message": "✅ YT-DLP Ultra Fast API is Running Smoothly!",
        "cache_size": len(stream_cache),
        "version": "3.0"
    }


# ---------------------------------------------------
# VIDEO INFO
# ---------------------------------------------------
@app.get("/info")
def info(url: str):
    try:
        ydl_opts = get_ydl_opts({"skip_download": True})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Thumbnail fallback
        thumbnail = info.get("thumbnail")
        if not thumbnail and info.get("thumbnails"):
            try:
                thumbnail = info["thumbnails"][-1]["url"]
            except Exception:
                thumbnail = "https://i.imgur.com/404.png"
        if not thumbnail:
            thumbnail = "https://i.imgur.com/404.png"

        formats = [
            {
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "filesize": f.get("filesize"),
                "quality": f.get("format_note"),
                "acodec": f.get("acodec"),
                "vcodec": f.get("vcodec"),
                "url": f.get("url"),
            }
            for f in info.get("formats", []) if f.get("url")
        ]

        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "channel": info.get("channel") or info.get("uploader"),
            "duration": info.get("duration"),
            "views": info.get("view_count"),
            "thumbnail": thumbnail,
            "formats": formats[:10],
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


# ---------------------------------------------------
# SEARCH
# ---------------------------------------------------
@app.get("/search")
def search(q: str = Query(..., description="Search query"), limit: int = 10):
    query = f"ytsearch{limit}:{q}"
    try:
        ydl_opts = get_ydl_opts({"extract_flat": True})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
        return {"results": info.get("entries", [])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------
# TRENDING
# ---------------------------------------------------
@app.get("/trending")
def trending(region: str = "BD", limit: int = 15):
    query = f"ytsearch{limit}:trending in {region}"
    try:
        ydl_opts = get_ydl_opts({"extract_flat": True})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
        return {"region": region, "trending": info.get("entries", [])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------
# DOWNLOAD (MP3 / MP4)
# ---------------------------------------------------
@app.get("/download")
def download(url: str, type: str = "video"):
    tmp_dir = tempfile.gettempdir()
    try:
        ydl_opts = get_ydl_opts({
            "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
            "format": "bestaudio/best" if type == "audio" else "best",
        })
        if type == "audio":
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if type == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        return FileResponse(
            filename,
            media_type="application/octet-stream",
            filename=os.path.basename(filename),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {e}")


# ---------------------------------------------------
# STREAM (Auto cache + cleanup)
# ---------------------------------------------------
@app.get("/stream")
def stream(url: str, quality: str = "best"):
    now = time.time()
    cleanup_cache()

    # Cached URL reuse
    if url in stream_cache and now - stream_cache[url]["time"] < CACHE_TTL:
        return stream_cache[url]["data"]

    try:
        ydl_opts = get_ydl_opts({"format": quality})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        stream_url = info.get("url")
        if not stream_url:
            raise Exception("Stream URL not found.")

        data = {"title": info.get("title"), "stream_url": stream_url}
        stream_cache[url] = {"time": now, "data": data}
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Stream error: {e}")


# ---------------------------------------------------
# HEALTH
# ---------------------------------------------------
@app.api_route("/health", methods=["GET", "HEAD"])
def health(request: Request):
    cleanup_cache()
    return {
        "status": "ok",
        "cache_size": len(stream_cache),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
