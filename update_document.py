from pymongo import MongoClient

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select database and collection
db = client["database_test1"]
collection = db["test1"]

# Update one document where name = "Sahil Khan"
result = collection.update_one(
    {"name": "Sahil Khan"},           # filter (which row to update)
    {"$set": {"city": "Bangalore"}}   # update operation
)

print(f"Matched: {result.matched_count}, Modified: {result.modified_count}")
