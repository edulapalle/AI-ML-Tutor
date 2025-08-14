

# pip install youtube-transcript-api yt-dlp

import os
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# === CONFIG ===
PLAYLIST_URL = "https://youtube.com/playlist?list=PLblh5JKOoLUICTaGLRoHQDuF_7q2GfuJF&si=P1OTlKtqQue8De_e"
OUTPUT_DIR = "statquest_transcripts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === STEP 1: Get all video IDs from the playlist ===
def get_video_ids(playlist_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'dump_single_json': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(playlist_url, download=False)
        return [entry['id'] for entry in info_dict['entries'] if entry]

video_ids = get_video_ids(PLAYLIST_URL)
print(f"Found {len(video_ids)} videos in the playlist.")

# === STEP 2: Download transcripts ===
def save_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        with open(os.path.join(OUTPUT_DIR, f"{video_id}.txt"), "w", encoding="utf-8") as f:
            for entry in transcript:
                f.write(entry['text'] + "\n")
        print(f"✅ Saved transcript for {video_id}")
    except (TranscriptsDisabled, NoTranscriptFound):
        print(f"❌ No transcript for {video_id}")

for vid in video_ids:
    save_transcript(vid)

print("🎯 All transcripts processed.")
