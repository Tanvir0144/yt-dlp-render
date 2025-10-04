from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import os, base64, tempfile

app = FastAPI(title="YT-DLP Super API", version="2.0")

# ---------------------------------------------------
# Common yt-dlp options (with cookie decode support)
# ---------------------------------------------------
def get_ydl_opts(extra_opts=None):
    opts = {"quiet": True, "noplaylist": True, "nocheckcertificate": True}
    cookies_b64 = os.getenv("COOKIES_B64")
    if cookies_b64:
        try:
            cookies_data = base64.b64decode(cookies_b64).decode("utf-8")
            with open("cookies.txt", "w", encoding="utf-8") as f:
                f.write(cookies_data)
            opts["cookiefile"] = "cookies.txt"
        except Exception as e:
            print("Cookie decode error:", e)
    if extra_opts:
        opts.update(extra_opts)
    return opts


@app.get("/")
def home():
    return {"message": "✅ YT-DLP Ultimate API is Running!", "version": "2.0"}


# ---------------------------------------------------
# VIDEO INFO / METADATA
# ---------------------------------------------------
@app.get("/info")
def info(url: str):
    try:
        ydl_opts = get_ydl_opts({"skip_download": True})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "duration": info.get("duration"),
            "view_count": info.get("view_count"),
            "thumbnail": info.get("thumbnail"),
            "formats": [
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
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------
# SEARCH (YouTube only)
# ---------------------------------------------------
@app.get("/search")
def search(q: str = Query(..., description="Search query"), limit: int = 5):
    query = f"ytsearch{limit}:{q}"
    ydl_opts = get_ydl_opts({"extract_flat": True})
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
        return {"results": info.get("entries", [])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------
# TRENDING (YouTube regional)
# ---------------------------------------------------
@app.get("/trending")
def trending(region: str = "BD", limit: int = 10):
    query = f"ytsearch{limit}:trending in {region}"
    ydl_opts = get_ydl_opts({"extract_flat": True})
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
        return {"region": region, "trending": info.get("entries", [])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------
# DOWNLOAD VIDEO / AUDIO (returns real file)
# ---------------------------------------------------
@app.get("/download")
def download(url: str, type: str = "video"):
    tmp_dir = tempfile.gettempdir()
    try:
        if type == "audio":
            ydl_opts = get_ydl_opts({
                "format": "bestaudio/best",
                "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            ydl_opts = get_ydl_opts({
                "format": "best",
                "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if type == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        if not os.path.exists(filename):
            raise FileNotFoundError("Download failed.")
        return FileResponse(
            filename,
            media_type="application/octet-stream",
            filename=os.path.basename(filename),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------
# STREAM (returns playable direct URL)
# ---------------------------------------------------
@app.get("/stream")
def stream(url: str, quality: str = "best"):
    try:
        ydl_opts = get_ydl_opts({"format": quality})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        stream_url = info.get("url")
        if not stream_url:
            raise Exception("Stream URL not found.")
        return {"title": info.get("title"), "stream_url": stream_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------
# HEALTH CHECK (for Render + UptimeRobot)
# ---------------------------------------------------
@app.api_route("/health", methods=["GET", "HEAD"])
def health(request: Request):
    return {"status": "ok"}
