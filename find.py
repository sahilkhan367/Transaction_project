from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # change URI if needed
db = client["Transaction_project"]
collection = db["users"]

# Create an index for fast search (important!)
collection.create_index("RFID")

# Fast find example
result = collection.find_one({"RFID": "1"})

if result:
    print("Found:", result)
else:
    print("No data found")
