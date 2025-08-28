from flask import Flask, request, render_template, redirect, url_for, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Transaction_project"]
collection = db["users"]

# ---- CREATE ----
@app.route('/')
def form():
    return render_template("form.html")

@app.route('/submit', methods=['POST'])
def submit():
    data = {
        "Name": request.form.get("Name"),
        "RFID": request.form.get("RFID"),
        "Employee ID": request.form.get("Employee ID")
    }
    collection.insert_one(data)
    return redirect(url_for('list_data'))

# ---- READ ----
@app.route('/list')
def list_data():
    data = list(collection.find())
    return render_template("list.html", data=data)

# ---- UPDATE ----
@app.route('/update/<id>', methods=['GET', 'POST'])
def update(id):
    if request.method == 'POST':
        collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "Name": request.form.get("Name"),
                "RFID": request.form.get("RFID"),
                "Employee ID": request.form.get("Employee ID")
            }}
        )
        return redirect(url_for('list_data'))
    else:
        doc = collection.find_one({"_id": ObjectId(id)})
        return render_template("update.html", doc=doc)

# ---- DELETE ----
@app.route('/delete/<id>')
def delete(id):
    collection.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('list_data'))


def create_log(data):
    db = client["Transaction_project"]
    collection = db["logs"]

    # Ensure a new unique _id is created every time
    if "_id" in data:
        del data["_id"]   # remove old _id

    # Optionally assign a fresh ObjectId
    data["_id"] = ObjectId()

    result = collection.insert_one(data)
    print("Inserted document ID:", result.inserted_id)


# ---- SIMPLE API ENDPOINT (Accept & Return Success) ----
@app.route('/api/submit', methods=['POST'])
def api_submit():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True)
    print(data)
    if not data:
        return jsonify({"status": "error", "message": "Invalid or empty JSON"}), 400

    rfid = data.get("RFID")
    if not rfid:
        return jsonify({"status": "error", "message": "Missing RFID field"}), 400

    # Ensure index for fast lookup
    collection.create_index("RFID")
    result = collection.find_one({"RFID": rfid})
    if result:
        merged_dict={**data, **result}
        now_time_date = datetime.now()
        merged_dict["date"] = now_time_date.strftime("%Y-%m-%d")   # e.g. "2025-08-28"
        merged_dict["time"] = now_time_date.strftime("%H:%M:%S")   # e.g. "10:45:33"
        print(merged_dict)
        create_log(merged_dict)

    if not result:
        return jsonify({
            "status": "error",
            "message": f"No data found for RFID {rfid}"
        }), 404   # Not Found

    # Convert ObjectId to string for JSON
    result["_id"] = str(result["_id"])

    return jsonify({
        "status": "success",
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
