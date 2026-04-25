import json
import os
import requests

# Constants
IMAGE_DIR = "album_images"
FILE_PATH = "2026a2_songs.json"

os.makedirs(IMAGE_DIR, exist_ok=True)


# Download a single image
def download_image(url, filename):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filename, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        print(f"Downloaded: {filename}")

    except Exception as e:
        print(f"Error downloading {url}: {e}")


#Read JSON and process images
def download_all_images():
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        songs = data.get("songs", [])
    else:
        songs = data

    for song in songs:
        img_url = song.get("img_url")

        if img_url:
            filename = os.path.join(
                IMAGE_DIR,
                os.path.basename(img_url)
            )

            if os.path.exists(filename):
                print(f"Already exists: {filename}")
                continue

            download_image(img_url, filename)



if __name__ == "__main__":
    download_all_images()