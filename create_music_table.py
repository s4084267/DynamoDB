# ASSESSMENT 2 - Project 
# AWS Cloud System Development 
import boto3


def expected_key_schema():
    return [
        {"AttributeName": "artist", "KeyType": "HASH"},
        {"AttributeName": "song_key", "KeyType": "RANGE"},
    ]


def initialize_table():
    # Create DynamoDB client (local)
    client = boto3.client(
        'dynamodb', 
        endpoint_url="http://localhost:8000",
        region_name="us-east-1"
    )

    # Create DynamoDB client (AWS)
    # client = boto3.client('dynamodb', region_name="us-east-1")

    table_definition = {
        "TableName": "Music",
        "BillingMode": "PAY_PER_REQUEST",
        "AttributeDefinitions": [
            {"AttributeName": "artist", "AttributeType": "S"},
            {"AttributeName": "song_key", "AttributeType": "S"},
            {"AttributeName": "year", "AttributeType": "S"},
            {"AttributeName": "album", "AttributeType": "S"},
            {"AttributeName": "title", "AttributeType": "S"}
        ],
        "KeySchema": [
            {"AttributeName": "artist", "KeyType": "HASH"},
            {"AttributeName": "song_key", "KeyType": "RANGE"}
        ],
        "LocalSecondaryIndexes": [
            {
                # Allows sorting an artist's songs chronologically by year.
                "IndexName": "ArtistYearIndex",
                "KeySchema": [
                    {"AttributeName": "artist", "KeyType": "HASH"},
                    {"AttributeName": "year", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"} 
            }
        ],
        "GlobalSecondaryIndexes": [
            {   
                "IndexName": "AlbumIndex",
                "KeySchema": [
                    {"AttributeName": "album", "KeyType": "HASH"},
                    {"AttributeName": "song_key", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            },
            {
                "IndexName": "TitleIndex",
                "KeySchema": [
                    {"AttributeName": "title", "KeyType": "HASH"},
                    {"AttributeName": "artist", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }
        ]
    }

    try:
        response = client.create_table(**table_definition)

        client.get_waiter('table_exists').wait(TableName="Music")

        return response['TableDescription']['TableStatus']
    except client.exceptions.ResourceInUseException:
        existing = client.describe_table(TableName="Music")["Table"]
        if existing.get("KeySchema") != expected_key_schema():
            return (
                "Table already exists with incompatible key schema. "
                "Expected HASH=artist and RANGE=song_key. "
                "Delete and recreate the table before importing."
            )
        return "Table already exists with expected schema."

if __name__ == "__main__":
    status = initialize_table()
    print(f"Current Status: {status}")