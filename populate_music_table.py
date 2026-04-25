# ASSESSMENT 2 - Project 
# AWS Cloud System Development

import json
from collections import Counter
from pathlib import Path

import boto3


TABLE_NAME = "Music"
DATA_FILE = "2026a2_songs.json"
SCRIPT_DIR = Path(__file__).resolve().parent


def load_songs(file_path):
	# Resolve data file from script folder so execution is independent of current working directory.
	file_path = Path(file_path)
	if not file_path.is_absolute():
		file_path = SCRIPT_DIR / file_path

	with open(file_path, "r", encoding="utf-8") as handle:
		raw = json.load(handle)

	if isinstance(raw, dict):
		songs = raw.get("songs", [])
	elif isinstance(raw, list):
		songs = raw
	else:
		raise ValueError("Unsupported JSON structure. Expected object or array.")

	if not isinstance(songs, list):
		raise ValueError("Expected songs collection to be a list.")

	return songs


def make_song_key(title, album):
	# Length-prefixed format avoids delimiter-collision ambiguity.
	return f"{len(title)}:{title}{len(album)}:{album}"


def analyze_songs(songs):
	required = ("title", "artist", "album", "year", "img_url")

	missing_field_count = 0
	for song in songs:
		for field in required:
			if field not in song or song[field] in (None, ""):
				missing_field_count += 1

	title_artist_counts = Counter((s["title"], s["artist"]) for s in songs)
	triplet_counts = Counter((s["title"], s["artist"], s["album"]) for s in songs)
	key_counts = Counter((s["artist"], make_song_key(s["title"], s["album"])) for s in songs)

	duplicate_title_artist = {k: v for k, v in title_artist_counts.items() if v > 1}
	duplicate_triplets = {k: v for k, v in triplet_counts.items() if v > 1}
	duplicate_primary_keys = {k: v for k, v in key_counts.items() if v > 1}

	print("Dataset analysis")
	print(f"- total songs: {len(songs)}")
	print(f"- unique titles: {len({s['title'] for s in songs})}")
	print(f"- unique artists: {len({s['artist'] for s in songs})}")
	print(f"- unique albums: {len({s['album'] for s in songs})}")
	print(f"- missing required fields: {missing_field_count}")
	print(f"- duplicate title+artist pairs: {len(duplicate_title_artist)}")
	print(f"- duplicate title+artist+album triplets: {len(duplicate_triplets)}")
	print(f"- duplicate DynamoDB primary keys (artist+song_key): {len(duplicate_primary_keys)}")

	if missing_field_count:
		raise ValueError("Dataset contains missing required fields.")

	# Any duplicate on the chosen primary key would cause item replacement.
	if duplicate_primary_keys:
		raise ValueError("Chosen key schema is not lossless for this dataset.")


def connect_table():
	# Create DynamoDB resource (local)
	# resource = boto3.resource(
	# 	"dynamodb",
	# 	endpoint_url="http://localhost:8000",
	# 	region_name="us-east-1",
	# )

	# Create DynamoDB resource (AWS)
	resource = boto3.resource("dynamodb", region_name="us-east-1")

	return resource.Table(TABLE_NAME)



def validate_table_schema(table):
	description = table.meta.client.describe_table(TableName=TABLE_NAME)["Table"]
	key_schema = description.get("KeySchema", [])
	expected = [
		{"AttributeName": "artist", "KeyType": "HASH"},
		{"AttributeName": "song_key", "KeyType": "RANGE"},
	]

	if key_schema != expected:
		raise RuntimeError(
			"Music table uses an incompatible key schema. "
			"Expected HASH=artist and RANGE=song_key. "
			"Recreate the table with create_music_table.py before importing."
		)


def count_items(table):
	response = table.scan(Select="COUNT")
	total = response["Count"]
	while "LastEvaluatedKey" in response:
		response = table.scan(Select="COUNT", ExclusiveStartKey=response["LastEvaluatedKey"])
		total += response["Count"]
	return total


def import_songs(table, songs):
	client_exceptions = table.meta.client.exceptions
	inserted = 0

	for song in songs:
		item = {
			"artist": song["artist"],
			"song_key": make_song_key(song["title"], song["album"]),
			"title": song["title"],
			"album": song["album"],
			"year": str(song["year"]),
			"img_url": song["img_url"],
		}

		try:
			# Conditional write guarantees no accidental overwrite of existing items.
			table.put_item(
				Item=item,
				ConditionExpression="attribute_not_exists(artist) AND attribute_not_exists(song_key)",
			)
			inserted += 1
		except client_exceptions.ConditionalCheckFailedException as error:
			raise ValueError(
				"Import aborted due to key collision with an existing item: "
				f"artist={item['artist']}, title={item['title']}, album={item['album']}"
			) from error

	return inserted


def main():
	songs = load_songs(DATA_FILE)
	analyze_songs(songs)

	table = connect_table()
	validate_table_schema(table)

	existing_count = count_items(table)
	if existing_count > 0:
		raise RuntimeError(
			"Music table already contains data. "
			"To run a full import again, delete and recreate the table first. "
			f"Current table item count: {existing_count}."
		)

	inserted = import_songs(table, songs)
	table_count = count_items(table)

	print("Import summary")
	print(f"- inserted songs: {inserted}")
	print(f"- table item count: {table_count}")

	if inserted != len(songs):
		raise RuntimeError("Inserted row count does not match source JSON row count.")

	if table_count < len(songs):
		raise RuntimeError("Table contains fewer rows than source JSON after import.")


if __name__ == "__main__":
	main()
