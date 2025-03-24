from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import webbrowser
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from scipy.signal import find_peaks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LinkRequest(BaseModel):
    link: str

def generate_spectrogram(audio_path: str) -> str:
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=400, detail=f"File not found: {audio_path}")

    y, sr = librosa.load(audio_path, sr=None)

    hop_length = 512
    D = librosa.amplitude_to_db(librosa.stft(y, hop_length=hop_length), ref=np.max)
    times = librosa.frames_to_time(np.arange(D.shape[1]), sr=sr, hop_length=hop_length)

    peaks = []
    step_size = 10
    max_peaks_per_time = 5
    for t in range(0, D.shape[1], step_size):
        magnitude = D[:, t]
        peak_indices, _ = find_peaks(magnitude, height=np.percentile(magnitude, 95))
        if len(peak_indices) > max_peaks_per_time:
            strongest_peaks = np.argsort(magnitude[peak_indices])[-max_peaks_per_time:]
            peak_indices = peak_indices[strongest_peaks]

        peaks.extend([(times[t], idx, magnitude[idx]) for idx in peak_indices])
    
    plt.figure(figsize=(10, 6))
    librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title(f'Spectrogram of {os.path.basename(audio_path)}')

    count = 0
    for peak in peaks:
        t, freq_idx, intensity = peak
        plt.plot(t, freq_idx, 'ro', markersize=3, zorder=3)
        print(count)
        count += 1

    img_bytes = BytesIO()
    plt.savefig(img_bytes, format='png')
    img_bytes.seek(0)

    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')

    print("Har")
    
    return img_base64

@app.post("/download_audio")
async def download_audio(request: LinkRequest):
    link = request.link

    os.makedirs("downloads", exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'ffmpeg_location': 'C:/ffmpeg',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            file_path = f"downloads/{info_dict['id']}.mp3"
            spectrogram_base64 = generate_spectrogram(file_path)
            
            return {
                "status": "success",
                "file_path": file_path,
                "spectrogram": spectrogram_base64
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")
