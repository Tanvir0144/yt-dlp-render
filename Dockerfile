# ---------- Base Python image ----------
FROM python:3.11-slim

# ---------- Set working directory ----------
WORKDIR /app

# ---------- Install ffmpeg + system deps ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ---------- Copy project files ----------
COPY . /app

# ---------- Install dependencies ----------
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Expose default port ----------
EXPOSE 8000

# ---------- Run FastAPI server ----------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
