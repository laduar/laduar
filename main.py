import os, io, time
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

# === CONFIGURE THIS ===
FOLDER_ID = "1xyepyNXc_j_ThL0A_vzfqTek5g4BRKJm"
VIDEO_PATH = "./videos"
UPLOAD_INTERVAL = 30 * 60  # every 30 minutes

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
]

def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_console()
    drive = build("drive", "v3", credentials=creds)
    youtube = build("youtube", "v3", credentials=creds)
    return drive, youtube

def download_videos(drive, path):
    os.makedirs(path, exist_ok=True)
    results = drive.files().list(
        q=f"'{FOLDER_ID}' in parents and mimeType contains 'video/'",
        fields="files(id,name)"
    ).execute()
    for f in results.get("files", []):
        fname = os.path.join(path, f["name"])
        if not os.path.exists(fname):
            request = drive.files().get_media(fileId=f["id"])
            fh = io.FileIO(fname, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            print("Downloaded:", f["name"])

def upload_videos(youtube, path):
    for fname in os.listdir(path):
        full = os.path.join(path, fname)
        if full.lower().endswith((".mp4", ".mov")):
            title = os.path.splitext(fname)[0].replace("_", " ")
            media = MediaFileUpload(full, mimetype="video/*", resumable=True)
            req = youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": "#shorts",
                        "tags": ["shorts"],
                        "categoryId": "22"
                    },
                    "status": {"privacyStatus": "public"}
                },
                media_body=media
            )
            resp = req.execute()
            print("Uploaded:", fname, "as", resp["id"])
            os.remove(full)

def main():
    drive, youtube = authenticate()
    while True:
        download_videos(drive, VIDEO_PATH)
        upload_videos(youtube, VIDEO_PATH)
        time.sleep(UPLOAD_INTERVAL)

if __name__ == "__main__":
    main()
