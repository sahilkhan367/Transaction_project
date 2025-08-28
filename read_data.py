from pymongo import MongoClient

# Connect to local MongoDB (default port 27017)
client = MongoClient("mongodb://localhost:27017/")

# Select database
db = client["transaction_project"]

# Select collection
collection = db["users"]

# Read all documents
documents = collection.find()

print("Data in testCollection:")
for doc in documents:
    print(doc)
