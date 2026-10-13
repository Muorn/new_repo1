#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: upload_drive.py output.mp4")
    src = Path(sys.argv[1])
    if not src.exists():
        raise FileNotFoundError(src)

    raw = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON")
    folder_id = os.environ.get("GDRIVE_REVIEW_FOLDER_ID")
    if not raw or not folder_id:
        raise SystemExit("Drive credentials/folder are not configured")

    info = json.loads(raw)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)

    metadata = {"name": src.name, "parents": [folder_id]}
    media = MediaFileUpload(str(src), mimetype="video/mp4", resumable=True)
    result = drive.files().create(body=metadata, media_body=media, fields="id,name,webViewLink").execute()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
