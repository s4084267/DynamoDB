# ASSESSMENT 2 - Project 
# AWS Cloud System Development 

import boto3
import os


TABLE_NAME = "Music"

BUCKET_NAME = "music-catalog-covers-s4084267"
REGION = "us-east-1"
S3_FOLDER_PREFIX = "album_covers/"

# The new base URL format for objects hosted in your S3 bucket
S3_BASE_URL = f"https://{BUCKET_NAME}.s3.amazonaws.com/{S3_FOLDER_PREFIX}"

def update_dynamodb_image_urls():
    
    # for aws dynamodb, use the following client configuration
    # dynamodb = boto3.resource('dynamodb', region_name=REGION)
    

    # For local DynamoDB testing, use the following client configuration
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url="http://localhost:8000",
        region_name=REGION
    )

    table = dynamodb.Table(TABLE_NAME)

    print(f"Starting database migration for table: {TABLE_NAME}...")
    print(f"Targeting new S3 Base URL: {S3_BASE_URL}\n")
    
    updated_count = 0

    # 1. Initiate the first Scan
    response = table.scan()
    items = response.get('Items', [])
    
    # Use a while loop to handle pagination (if the table is very large)
    while True:
        for item in items:
            old_url = item.get('img_url', '')
            
            # If the URL is empty or already updated to S3, skip it to save read/write capacity
            if not old_url or S3_BASE_URL in old_url:
                continue
                
            # 2. Extract just the filename (e.g., 'divide.jpg') from the old URL
            filename = os.path.basename(old_url)
            
            # 3. Construct the brand new S3 URL
            new_s3_url = f"{S3_BASE_URL}{filename}"
            
            print(f"Updating song: {item.get('title', 'Unknown Title')}")
            print(f"  Old URL: {old_url}")
            print(f"  New URL: {new_s3_url}")
            
            # 4. Update the item in DynamoDB safely using its exact Primary Keys
            table.update_item(
                Key={
                    'artist': item['artist'],
                    'song_key': item['song_key']
                },
                UpdateExpression="SET img_url = :new_url",
                ExpressionAttributeValues={
                    ':new_url': new_s3_url
                }
            )
            updated_count += 1

        # 5. Check if there are more items to scan (Pagination)
        if 'LastEvaluatedKey' in response:
            print("Fetching next page of database results...")
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items = response.get('Items', [])
        else:
            break # No more pages, exit the loop

    print(f"\nMigration complete. Successfully updated {updated_count} records.")

if __name__ == "__main__":
    update_dynamodb_image_urls()