from fastapi import FastAPI
import yt_dlp

app = FastAPI()

@app.get("/")
def home():
    return {"message": "YT-DLP Super API Running on Render!"}

@app.get("/download")
def download(url: str):
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "duration": info.get("duration"),
            "views": info.get("view_count"),
            "thumbnail": info.get("thumbnail"),
            "formats": info.get("formats")[:5],
            "url": info.get("webpage_url"),
        }

@app.get("/search")
def search(q: str, limit: int = 5):
    url = f"ytsearch{limit}:{q}"
    ydl_opts = {"quiet": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {"results": info["entries"]}

@app.get("/trending")
def trending(region: str = "US"):
    url = f"https://www.youtube.com/feed/trending?gl={region}"
    ydl_opts = {"quiet": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {"trending": info["entries"][:10]}

@app.get("/play")
def play(url: str):
    ydl_opts = {"quiet": True, "format": "best"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "stream_url": info["url"]
        }
