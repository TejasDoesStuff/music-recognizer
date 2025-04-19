from fastapi import FastAPI, HTTPException
from routes import recognize
from pydantic import BaseModel
import webbrowser
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import hashlib 
from db import database
from models import songs, fingerprints
import re

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from scipy.signal import find_peaks

app = FastAPI()

app.include_router(recognize.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

class LinkRequest(BaseModel):
    link: str

# download audio
@app.post("/download_audio")
async def download_audio(req: LinkRequest):
    link = req.link

    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)

            filename = ydl.prepare_filename(info_dict)
            file_path = os.path.splitext(filename)[0] + '.mp3'

            cleaned_title = re.sub(r'[^\w\s-]', '', info_dict['title'])
            cleaned_title = re.sub(r'[-\s]+', ' ', cleaned_title).strip()
            cleaned_path = f"downloads/{cleaned_title}.mp3"

            if file_path != cleaned_path:
                try:
                    os.replace(file_path, cleaned_path)
                    file_path = cleaned_path
                except FileNotFoundError:
                    raise HTTPException(status_code=500, detail=f"Downloaded file not found: {file_path}")

            spectrogram, hashes = generate_spectrogram(file_path)

            await add_to_db(info_dict['title'], info_dict['uploader'], hashes, cleaned_path)

            return {
                "status": "success",
                "file_path": file_path,
                "spectrogram": spectrogram
            }
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")

# spectrogram stuff
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
        peak_indices, _ = find_peaks(magnitude, height=np.percentile(magnitude, 99.99))
        if len(peak_indices) > max_peaks_per_time:
            strongest_peaks = np.argsort(magnitude[peak_indices])[-max_peaks_per_time:]
            peak_indices = peak_indices[strongest_peaks]

        peaks.extend([(times[t], idx, magnitude[idx]) for idx in peak_indices])
    
    # print("Detected Peaks:", peaks)

    count = 0
    hashes = []
    for i in range(len(peaks) - 1):
        t1, freq1, _ = peaks[i]
        t2, freq2, _ = peaks[i + 1]

        time_diff = t2 - t1
        freq_diff = freq2 - freq1

        peak_hash = hash_pair(time_diff, freq_diff)
        hashes.append((peak_hash, t1))
        count += 1
    print(count)

    # print("Generated Hashes:", hashes)

    plt.figure(figsize=(10, 6))
    librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title(f'Spectrogram of {os.path.basename(audio_path)}')

    count = 0
    for peak in peaks:
        t, freq_idx, intensity = peak
        plt.plot(t, freq_idx, 'ro', markersize=3, zorder=3)
        # print(count)
        # count += 1

    img_bytes = BytesIO()
    plt.savefig(img_bytes, format='png')
    img_bytes.seek(0)

    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    
    return img_base64, hashes

# hash stuff
def hash_pair(time_diff, freq_diff):
    pair_string = f"{time_diff}_{freq_diff}"
    return hashlib.sha256(pair_string.encode('utf-8')).hexdigest()

# add to db
async def add_to_db(song_title: str, artist: str, hashes: list[tuple[str, float]], cleaned_path: str):
    print(f"adding {song_title}")

    query = songs.select().where(songs.c.title == song_title and songs.c.artist == artist)
    existing = await database.fetch_one(query)

    if existing:
        print(f"Song '{song_title}' already exists with ID {existing['id']}")

        if os.path.exists(cleaned_path):
            os.remove(cleaned_path)
            print(f"Deleted downloaded file: {cleaned_path}")
        return existing['id']

    query = songs.insert().values(title=song_title, artist=artist)
    song_id = await database.execute(query)
    print(f"Inserted song {song_title} with ID {song_id}")

    for h, t in hashes:
        await database.execute(fingerprints.insert().values(
            song_id=song_id,
            hash=h,
            offset_time=t
        ))

    print(f"Saved {len(hashes)} fingerprints for {song_title}")

    if os.path.exists(cleaned_path):
        os.remove(cleaned_path)
        print(f"Deleted downloaded file: {cleaned_path}")

    return song_id