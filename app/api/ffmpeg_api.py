# app/api/ffmpeg_api.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import subprocess
import os
import uuid
from pathlib import Path

app = FastAPI()

# Configuration
INPUT_DIR = "inputs"
OUTPUT_DIR = "outputs"
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/merge")
async def merge_video_audio(
    video_file: UploadFile = File(...),
    audio_file: UploadFile = File(...),
    output_format: str = "mp4"
):
    """Merge video and audio streams"""
    try:
        # Save uploaded files
        video_path = Path(INPUT_DIR) / f"video_{uuid.uuid4().hex}.tmp"
        audio_path = Path(INPUT_DIR) / f"audio_{uuid.uuid4().hex}.tmp"
        output_path = Path(OUTPUT_DIR) / f"output_{uuid.uuid4().hex}.{output_format}"

        with open(video_path, "wb") as vf:
            vf.write(await video_file.read())
        
        with open(audio_path, "wb") as af:
            af.write(await audio_file.read())

        # Run FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-strict", "experimental",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True)

        # Cleanup input files
        video_path.unlink()
        audio_path.unlink()

        return FileResponse(
            output_path,
            media_type=f"video/{output_format}",
            filename=f"merged.{output_format}"
        )

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup if files exist
        if 'video_path' in locals() and video_path.exists():
            video_path.unlink()
        if 'audio_path' in locals() and audio_path.exists():
            audio_path.unlink()

@app.post("/convert-to-mp3")
async def convert_to_mp3(
    input_file: UploadFile = File(...),
    bitrate: str = "192k"
):
    """Convert any audio file to MP3"""
    try:
        # Save uploaded file
        input_path = Path(INPUT_DIR) / f"input_{uuid.uuid4().hex}.tmp"
        output_path = Path(OUTPUT_DIR) / f"output_{uuid.uuid4().hex}.mp3"

        with open(input_path, "wb") as f:
            f.write(await input_file.read())

        # Run FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-codec:a", "libmp3lame",
            "-b:a", bitrate,
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True)

        # Cleanup input file
        input_path.unlink()

        return FileResponse(
            output_path,
            media_type="audio/mpeg",
            filename="converted.mp3"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'input_path' in locals() and input_path.exists():
            input_path.unlink()

@app.on_event("shutdown")
def cleanup():
    """Cleanup all files on shutdown"""
    for f in Path(INPUT_DIR).glob("*"):
        f.unlink()
    for f in Path(OUTPUT_DIR).glob("*"):
        f.unlink()