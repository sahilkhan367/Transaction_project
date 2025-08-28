from pymongo import MongoClient

# Connect to local MongoDB (default port 27017)
client = MongoClient("mongodb://localhost:27017/")

# Select database (it will be created automatically if not exist)
db = client["database_test1"]

# Select collection (also auto-created if not exist)
collection = db["test1"]

# Data to insert (dictionary)
data = {
    "name": "Sahil Khan",
    "city": "Davangere",
    "role": "IoT Engineer"
}

# Insert one document
result = collection.insert_one(data)

print("Inserted document ID:", result.inserted_id)
