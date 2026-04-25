import boto3
import bcrypt

# Constants
TABLE_NAME = "Login"

# Create DynamoDB client (local)
# client = boto3.client(
#     'dynamodb',
#     endpoint_url="http://localhost:8000",
#     region_name="us-east-1"
# )

# Create DynamoDB client (AWS)
client = boto3.client('dynamodb', region_name="us-east-1")

def expected_key_schema():
    return [
        {"AttributeName": "email", "KeyType": "HASH"}
    ]


def initialize_table():
    table_definition = {
        "TableName": TABLE_NAME,
        "KeySchema": expected_key_schema(),
        "AttributeDefinitions": [
            {"AttributeName": "email", "AttributeType": "S"}
        ],
        "BillingMode": "PAY_PER_REQUEST"
    }

    try:
        response = client.create_table(**table_definition)

        # Wait until table is ready
        client.get_waiter('table_exists').wait(TableName=TABLE_NAME)

        return response['TableDescription']['TableStatus']

    except client.exceptions.ResourceInUseException:
        existing = client.describe_table(TableName=TABLE_NAME)["Table"]

        if existing.get("KeySchema") != expected_key_schema():
            return (
                "Table exists but schema is incompatible. "
                "Delete and recreate the table."
            )

        return "Table already exists with correct schema."


def hash_password(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


def populate_table():
    items = []

    for i in range(10):
        email = f"s400000{i}@student.rmit.edu.au"
        username = f"Sajad Ali Akbari{i}"
        password = f"{i}123456"

        item = {
            "email": {"S": email},
            "username": {"S": username},
            "password": {"S": hash_password(password)}
        }

        items.append(item)

    for item in items:
        print(f"Adding item: {item['email']['S']}")
        client.put_item(
            TableName=TABLE_NAME,
            Item=item
        )


if __name__ == "__main__":
    status = initialize_table()
    print(f"Table Status: {status}")

    populate_table()