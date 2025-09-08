from flask import Flask, request, render_template, redirect, url_for, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from collections import defaultdict
import pymongo 
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)  # <-- allow all origins

lock = threading.Lock()
priority_active = threading.Event()

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Transaction_project"]
collection = db["users"]



def process_all_logs(logs, result_container):
    grouped_logs = defaultdict(list)
    for log in logs:
        grouped_logs[(log["Name"], log["RFID"], log["date"])].append(log)
    
    summaries = []
    
    for (name, rfid, date), person_logs in grouped_logs.items():
        logs_sorted = sorted(person_logs, key=lambda x: x["time"])
        
        for log in logs_sorted:
            log["datetime"] = datetime.strptime(f'{log["date"]} {log["time"]}', "%Y-%m-%d %H:%M:%S")
        
        login_time, logout_time = None, None
        total_login, errors = 0, []
        in_time = None
        
        for log in logs_sorted:
            action = log["IN/OUT"]

            if action == "IN":
                if in_time is None:
                    in_time = log["datetime"]   # start session
                    if login_time is None:      # first login of the day
                        login_time = in_time
                else:
                    errors.append(f"Duplicate IN at {log['time']}")
            
            elif action == "OUT":
                if in_time is not None:
                    total_login += (log["datetime"] - in_time).total_seconds()
                    logout_time = log["datetime"]   # last valid logout
                    in_time = None
                else:
                    errors.append(f"Unexpected OUT at {log['time']}")
        
        # If day ends with an IN but no OUT
        if in_time is not None:
            errors.append(f"Missing OUT after {in_time.strftime('%H:%M:%S')}")
        
        # Calculate break time and total duration
        total_break = 0
        if login_time and logout_time:
            total_duration = (logout_time - login_time).total_seconds()
            total_break = total_duration - total_login
            time_spent = str(logout_time - login_time)
        else:
            time_spent = None
        
        summaries.append({
            "name": name,
            "rfid": rfid,
            "date": date,
            "login_time": login_time.strftime("%H:%M:%S") if login_time else None,
            "logout_time": logout_time.strftime("%H:%M:%S") if logout_time else None,
            "Effective_login": str(timedelta(seconds=total_login)),
            "Break_hours": str(timedelta(seconds=total_break)),
            "Total_login": time_spent,
            "errors": errors
        })
    
    # store result in shared container
    result_container["summary"] = summaries




@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
    
    collection.insert_one(data)
    return jsonify({"status": "success", "message": "Data saved"}), 201

# ---------- READ ----------
@app.route('/list', methods=['GET'])
def get_list():
    docs = list(collection.find({}, {"_id": 1, "Name": 1, "RFID": 1, "Employee ID": 1}))
    # convert ObjectId to string
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify(docs)

# ---------- UPDATE ----------
@app.route('/update/<id>', methods=['PUT'])
def update(id):
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
    
    result = collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "Name": data.get("Name"),
            "RFID": data.get("RFID"),
            "Employee ID": data.get("Employee ID")
        }}
    )
    if result.modified_count > 0:
        return jsonify({"status": "success", "message": "Record updated"})
    return jsonify({"status": "error", "message": "Record not found"}), 404

# ---------- DELETE ----------
@app.route('/delete/<id>', methods=['DELETE'])
def delete(id):
    result = collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count > 0:
        return jsonify({"status": "success", "message": "Record deleted"})
    return jsonify({"status": "error", "message": "Record not found"}), 404

# ---------- LOGS ----------
def create_log(data):
    logs_collection = db["logs"]

    if "_id" in data:
        del data["_id"]   # avoid duplicate IDs
    data["_id"] = ObjectId()

    result = logs_collection.insert_one(data)
    print("Inserted document ID:", result.inserted_id)

@app.route("/logs", methods=["GET"])
def view_logs():
    logs_collection = db["logs"]

    # --- Read query parameters ---
    names = request.args.getlist("name")   # multiple ?name=Alice&name=Bob
    date = request.args.get("date")        # e.g. "2025-09-08"

    # --- Build filter dynamically ---
    query = {}
    if names:
        query["Name"] = {"$in": names}
    if date:
        query["date"] = date

    # --- Fetch filtered logs ---
    logs = list(logs_collection.find(query, {"_id": 0}))

    # --- Process logs with your function ---
    result_container = {}
    thread = threading.Thread(target=process_all_logs, args=(logs, result_container))
    thread.start()
    thread.join()

    return jsonify(result_container.get("summary", []))

# ---- SIMPLE API ENDPOINT (Accept & Return Success) ----
@app.route('/api/submit', methods=['POST'])
def api_submit():
    global priority_active
    priority_active.set()
    with lock:
        try:
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
                thread = threading.Thread(target=create_log, args=(merged_dict,))    #creats background jobs to creat logs
                thread.start()
                #create_log(merged_dict)
        
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
        finally:
            priority_active.clear()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
