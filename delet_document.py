from pymongo import MongoClient

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select database and collection
db = client["database_test1"]
collection = db["test1"]

# Delete one document that matches the filter
result = collection.delete_one({"name": "Sahil Khan"})

print(f"Deleted {result.deleted_count} document.")
