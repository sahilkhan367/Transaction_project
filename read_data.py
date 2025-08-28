from pymongo import MongoClient

# Connect to local MongoDB (default port 27017)
client = MongoClient("mongodb://localhost:27017/")

# Select database
db = client["Transaction_project"]

# Select collection
collection = db["logs"]

# Read all documents
documents = collection.find()

print("Data in testCollection:")
for doc in documents:
    print(doc)
