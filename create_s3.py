# ASSESSMENT 2 - Project 
# AWS Cloud System Development

import boto3
from botocore.exceptions import ClientError

def create_s3_bucket(bucket_name, region="us-east-1"):
    print(f"Attempting to create bucket '{bucket_name}' in {region}...")
    try:
        # Boto3 requires a different syntax for us-east-1 compared to all other regions.
        if region == "us-east-1":
            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(
                Bucket=bucket_name, 
                CreateBucketConfiguration=location
            )
            
        print(f"successfully created: {bucket_name}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyExists':
            print(f"The bucket name '{bucket_name}' is already taken by someone else in AWS.")
        elif error_code == 'BucketAlreadyOwnedByYou':
            print(f"You already own the bucket '{bucket_name}'.")
        else:
            print(f"Error creating bucket: {e}")
        return False

if __name__ == "__main__":
    #i used my studentID to make the bucket name unique, change the bucket name if you want to run this program
    TARGET_BUCKET_NAME = "music-catalog-covers-s4084267" 
    TARGET_REGION = "us-east-1"
    
    print(f"Attempting to create bucket '{TARGET_BUCKET_NAME}' in {TARGET_REGION}...")
    create_s3_bucket(TARGET_BUCKET_NAME, TARGET_REGION)