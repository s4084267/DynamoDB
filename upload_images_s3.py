# ASSESSMENT 2 - Project 
# AWS Cloud System Development

import json
import os
import requests
import boto3
from botocore.exceptions import ClientError

# Constants
FILE_PATH = "2026a2_songs.json"
# make sure you already have created the bucket using create_s3.py and update the bucket 
# name with your own bucket name if you want to run this program
BUCKET_NAME = "music-catalog-covers-s4084267" 
REGION = "us-east-1"
S3_FOLDER_PREFIX = "album_covers/" # put all images in an "album_covers" folder in the bucket to keep it organised


client = boto3.client('s3', region_name=REGION)

def upload_image_to_s3(url, bucket, s3_key):
    print("downloading images from url and uploading to s3...")
    try:
        #get the image as a stream from old url
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # get the content type for s3
        content_type = response.headers.get('Content-Type', 'image/jpeg')

        #upload the image stream to s3 with content type
        client.upload_fileobj(
            Fileobj=response.raw,
            Bucket=bucket,
            Key=s3_key,
            ExtraArgs={'ContentType': content_type}
        )
        print(f"Uploaded: {s3_key}")

    except requests.exceptions.RequestException as e:
        print(f"can't download {url}: {e}")
    except ClientError as e:
        print(f"can't upload {s3_key}: {e}")


def process_and_upload():
    print("reading JSON file and processing images...")
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    #handle different possible json structures
    if isinstance(data, dict):
        songs = data.get("songs", [])
    else:
        songs = data

    for song in songs:
        img_url = song.get("img_url")

        if img_url:
            #get the filename from url
            filename = os.path.basename(img_url)

            #make the s3 key
            s3_key = f"{S3_FOLDER_PREFIX}{filename}"

            upload_image_to_s3(img_url, BUCKET_NAME, s3_key)


if __name__ == "__main__":
    print(f"Starting S3 upload to bucket: {BUCKET_NAME}...")
    process_and_upload()
    print("Process complete.")