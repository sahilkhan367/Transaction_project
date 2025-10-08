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
client = MongoClient("mongodb://10.80.3.148:27017/")
db = client["Transaction_project"]
collection = db["users"]
cabin_collection = db["cabins"]



from collections import defaultdict
from datetime import datetime, timedelta


from collections import defaultdict
from datetime import datetime, timedelta

# def process_all_logs(logs, result_container, query_name=None, query_rfid=None, query_date=None, query_cabin_id=None):
#     """
#     logs: list of log dicts (may be empty)
#     result_container: dict used to store "summary"
#     query_name: str or list of names (from query)
#     query_rfid: str or list of rfids (from query)
#     query_date: str date (from query)
#     """

#     # Normalize query inputs to lists
#     def to_list(x):
#         if x is None:
#             return []
#         if isinstance(x, list):
#             return x
#         if isinstance(x, str) and "," in x:
#             return [i.strip() for i in x.split(",") if i.strip()]
#         return [x]

#     q_names = to_list(query_name)
#     q_rfids = to_list(query_rfid)
#     q_date = query_date if query_date else ""

#     # If no logs at all → return Absent rows using original query details
#     if not logs:
#         summaries = []
#         if q_names and q_rfids and len(q_names) == len(q_rfids):
#             for n, r in zip(q_names, q_rfids):
#                 summaries.append({
#                     "name": n,
#                     "rfid": r,
#                     "date": q_date,
#                     "login_time": "",
#                     "logout_time": "",
#                     "Effective_login": "",
#                     "Break_hours": "",
#                     "Total_login": "",
#                     "errors": "Absent"
#                 })
#         elif q_names:
#             first_rfid = q_rfids[0] if q_rfids else ""
#             for n in q_names:
#                 summaries.append({
#                     "name": n,
#                     "rfid": first_rfid,
#                     "date": q_date,
#                     "login_time": "",
#                     "logout_time": "",
#                     "Effective_login": "",
#                     "Break_hours": "",
#                     "Total_login": "",
#                     "errors": "Absent"
#                 })
#         elif q_rfids:
#             first_name = q_names[0] if q_names else ""
#             for r in q_rfids:
#                 summaries.append({
#                     "name": first_name,
#                     "rfid": r,
#                     "date": q_date,
#                     "login_time": "",
#                     "logout_time": "",
#                     "Effective_login": "",
#                     "Break_hours": "",
#                     "Total_login": "",
#                     "errors": "Absent"
#                 })
#         else:
#             summaries.append({
#                 "name": "",
#                 "rfid": "",
#                 "date": q_date,
#                 "login_time": "",
#                 "logout_time": "",
#                 "Effective_login": "",
#                 "Break_hours": "",
#                 "Total_login": "",
#                 "errors": "Absent"
#             })

#         result_container["summary"] = summaries
#         return

#     # --- Normal processing when logs exist ---
#     grouped_logs = defaultdict(list)
#     for log in logs:
#         grouped_logs[(log.get("Name", ""), log.get("RFID", ""), log.get("date", ""))].append(log)
    
#     summaries = []
#     present_pairs = set()
#     present_names = set()
#     present_rfids = set()

#     for (name, rfid, date), person_logs in grouped_logs.items():
#         present_pairs.add((name, rfid))
#         present_names.add(name)
#         present_rfids.add(rfid)

#         logs_sorted = sorted(person_logs, key=lambda x: x.get("time", ""))
        
#         # defensive datetime parsing
#         for log in logs_sorted:
#             dt_str_date = log.get("date", "")
#             dt_str_time = log.get("time", "")
#             try:
#                 log["datetime"] = datetime.strptime(f'{dt_str_date} {dt_str_time}', "%Y-%m-%d %H:%M:%S")
#             except Exception:
#                 log["datetime"] = None
        
#         login_time, logout_time = None, None
#         total_login = 0
#         errors = []
#         in_time = None
        
#         for log in logs_sorted:
#             action = log.get("IN/OUT", "")
#             dt = log.get("datetime")

#             if action == "IN":
#                 if in_time is None:
#                     if dt:
#                         in_time = dt
#                         if login_time is None:
#                             login_time = in_time
#                     else:
#                         errors.append(f"Bad IN datetime at {log.get('time', '')}")
#                 else:
#                     errors.append(f"Duplicate IN at {log.get('time', '')}")
            
#             elif action == "OUT":
#                 if in_time is not None and dt:
#                     total_login += (dt - in_time).total_seconds()
#                     logout_time = dt
#                     in_time = None
#                 else:
#                     errors.append(f"Unexpected OUT at {log.get('time', '')}")
        
#         if in_time is not None:
#             try:
#                 errors.append(f"Missing OUT after {in_time.strftime('%H:%M:%S')}")
#             except Exception:
#                 errors.append("Missing OUT after unknown time")
        
#         total_break = 0
#         if login_time and logout_time:
#             total_duration = (logout_time - login_time).total_seconds()
#             total_break = total_duration - total_login
#             time_spent = str(logout_time - login_time)
#         else:
#             time_spent = ""
        
#         summaries.append({
#             "name": name,
#             "rfid": rfid,
#             "date": date,
#             "login_time": login_time.strftime("%H:%M:%S") if login_time else "",
#             "logout_time": logout_time.strftime("%H:%M:%S") if logout_time else "",
#             "Effective_login": str(timedelta(seconds=total_login)) if total_login else "",
#             "Break_hours": str(timedelta(seconds=total_break)) if total_break else "",
#             "Total_login": time_spent,
#             "errors": errors if errors else "Absent"
#         })

#     # --- Add Absent rows for requested names/rfids that weren't present in DB result --- #
#     # Pairwise when lengths match
#     if q_names and q_rfids and len(q_names) == len(q_rfids):
#         for n, r in zip(q_names, q_rfids):
#             if (n, r) not in present_pairs:
#                 summaries.append({
#                     "name": n,
#                     "rfid": r,
#                     "date": q_date,
#                     "login_time": "",
#                     "logout_time": "",
#                     "Effective_login": "",
#                     "Break_hours": "",
#                     "Total_login": "",
#                     "errors": "Absent"
#                 })
#     # If only names requested -> add per name not present
#     elif q_names:
#         first_rfid = q_rfids[0] if q_rfids else ""
#         for n in q_names:
#             if n not in present_names:
#                 summaries.append({
#                     "name": n,
#                     "rfid": first_rfid,
#                     "date": q_date,
#                     "login_time": "",
#                     "logout_time": "",
#                     "Effective_login": "",
#                     "Break_hours": "",
#                     "Total_login": "",
#                     "errors": "Absent"
#                 })
#     # If only rfids requested -> add per rfid not present
#     elif q_rfids:
#         first_name = q_names[0] if q_names else ""
#         for r in q_rfids:
#             if r not in present_rfids:
#                 summaries.append({
#                     "name": first_name,
#                     "rfid": r,
#                     "date": q_date,
#                     "login_time": "",
#                     "logout_time": "",
#                     "Effective_login": "",
#                     "Break_hours": "",
#                     "Total_login": "",
#                     "errors": "Absent"
#                 })

#     result_container["summary"] = summaries








def process_all_logs(logs, result_container, query_name=None, query_rfid=None, query_date=None, query_cabin_id=None):
    """
    logs: list of log dicts (may be empty)
    result_container: dict used to store "summary"
    query_name: str or list of names (from query)
    query_rfid: str or list of rfids (from query)
    query_date: str date (from query)
    """

    # Normalize query inputs to lists
    def to_list(x):
        if x is None:
            return []
        if isinstance(x, list):
            return x
        if isinstance(x, str) and "," in x:
            return [i.strip() for i in x.split(",") if i.strip()]
        return [x]

    q_names = to_list(query_name)
    q_rfids = to_list(query_rfid)
    q_cabin_id = to_list(query_cabin_id)
    q_date = query_date if query_date else ""
    print("____q_cabin_id_____", q_cabin_id)

    # If no logs at all → return Absent rows using original query details
    if not logs:
        summaries = []
        if q_names and q_rfids and len(q_names) == len(q_rfids):
            for n, r in zip(q_names, q_rfids):
                summaries.append({
                    "name": n,
                    "rfid": r,
                    "date": q_date,
                    "log_cabin": q_cabin_id,
                    "login_time": "",
                    "logout_time": "",
                    "Effective_login": "",
                    "Break_hours": "",
                    "Total_login": "",
                    "errors": "Absent"
                })
        elif q_names:
            first_rfid = q_rfids[0] if q_rfids else ""
            for n in q_names:
                summaries.append({
                    "name": n,
                    "rfid": first_rfid,
                    "date": q_date,
                    "login_time": "",
                    "log_cabin": q_cabin_id,
                    "logout_time": "",
                    "Effective_login": "",
                    "Break_hours": "",
                    "Total_login": "",
                    "errors": "Absent"
                })
        elif q_rfids:
            first_name = q_names[0] if q_names else ""
            for r in q_rfids:
                summaries.append({
                    "name": first_name,
                    "rfid": r,
                    "date": q_date,
                    "login_time": "",
                    "log_cabin": q_cabin_id,
                    "logout_time": "",
                    "Effective_login": "",
                    "Break_hours": "",
                    "Total_login": "",
                    "errors": "Absent"
                })
        else:
            summaries.append({
                "name": "",
                "rfid": "",
                "date": q_date,
                "login_time": "",
                "log_cabin": q_cabin_id,
                "logout_time": "",
                "Effective_login": "",
                "Break_hours": "",
                "Total_login": "",
                "errors": "Absent"
            })

        result_container["summary"] = summaries
        return

    # --- Normal processing when logs exist ---
    grouped_logs = defaultdict(list)
    for log in logs:
        grouped_logs[(log.get("Name", ""), log.get("RFID", ""), log.get("date", ""))].append(log)
    
    summaries = []
    present_pairs = set()
    present_names = set()
    present_rfids = set()

    for (name, rfid, date), person_logs in grouped_logs.items():
        present_pairs.add((name, rfid))
        present_names.add(name)
        present_rfids.add(rfid)

        logs_sorted = sorted(person_logs, key=lambda x: x.get("time", ""))
        
        # defensive datetime parsing
        for log in logs_sorted:
            dt_str_date = log.get("date", "")
            dt_str_time = log.get("time", "")
            try:
                log["datetime"] = datetime.strptime(f'{dt_str_date} {dt_str_time}', "%Y-%m-%d %H:%M:%S")
            except Exception:
                log["datetime"] = None
        
        login_time, logout_time = None, None
        total_login = 0
        errors = []
        in_time = None
        
        for log in logs_sorted:
            action = log.get("IN/OUT", "")
            dt = log.get("datetime")

            if action == "IN":
                if in_time is None:
                    if dt:
                        in_time = dt
                        if login_time is None:
                            login_time = in_time
                    else:
                        errors.append(f"Bad IN datetime at {log.get('time', '')}")
                else:
                    errors.append(f"Duplicate IN at {log.get('time', '')}")
            
            elif action == "OUT":
                if in_time is not None and dt:
                    total_login += (dt - in_time).total_seconds()
                    logout_time = dt
                    in_time = None
                else:
                    errors.append(f"Unexpected OUT at {log.get('time', '')}")
        
        if in_time is not None:
            try:
                errors.append(f"Missing OUT after {in_time.strftime('%H:%M:%S')}")
            except Exception:
                errors.append("Missing OUT after unknown time")
        
        total_break = 0
        if login_time and logout_time:
            total_duration = (logout_time - login_time).total_seconds()
            total_break = total_duration - total_login
            time_spent = str(logout_time - login_time)
        else:
            time_spent = ""
        
        summaries.append({
            "name": name,
            "rfid": rfid,
            "date": date,
            "login_time": login_time.strftime("%H:%M:%S") if login_time else "",
            "logout_time": logout_time.strftime("%H:%M:%S") if logout_time else "",
            "Effective_login": str(timedelta(seconds=total_login)) if total_login else "",
            "Break_hours": str(timedelta(seconds=total_break)) if total_break else "",
            "Total_login": time_spent,
            "errors": errors if errors else "Absent"
        })

    # --- Add Absent rows for requested names/rfids that weren't present in DB result --- #
    # Pairwise when lengths match
    if q_names and q_rfids and len(q_names) == len(q_rfids):
        for n, r in zip(q_names, q_rfids):
            if (n, r) not in present_pairs:
                summaries.append({
                    "name": n,
                    "rfid": r,
                    "date": q_date,
                    "login_time": "",
                    "logout_time": "",
                    "Effective_login": "",
                    "Break_hours": "",
                    "Total_login": "",
                    "errors": "Absent"
                })
    # If only names requested -> add per name not present
    elif q_names:
        first_rfid = q_rfids[0] if q_rfids else ""
        for n in q_names:
            if n not in present_names:
                summaries.append({
                    "name": n,
                    "rfid": first_rfid,
                    "date": q_date,
                    "login_time": "",
                    "logout_time": "",
                    "Effective_login": "",
                    "Break_hours": "",
                    "Total_login": "",
                    "errors": "Absent"
                })
    # If only rfids requested -> add per rfid not present
    elif q_rfids:
        first_name = q_names[0] if q_names else ""
        for r in q_rfids:
            if r not in present_rfids:
                summaries.append({
                    "name": first_name,
                    "rfid": r,
                    "date": q_date,
                    "login_time": "",
                    "logout_time": "",
                    "Effective_login": "",
                    "Break_hours": "",
                    "Total_login": "",
                    "errors": "Absent"
                })

    result_container["summary"] = summaries












@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
    
    collection.insert_one(data)
    return jsonify({"status": "success", "message": "Data saved"}), 201


@app.route('/add_cabin', methods=['POST'])
def add_cabin():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
    
    cabin_collection.insert_one(data)
    return jsonify({"status": "success", "message": "Data saved"}), 201





# ---------- READ ----------
@app.route('/list', methods=['GET'])
def get_list():
    docs = list(collection.find(
        {},
        {
            "_id": 1,
            "Name": 1,
            "RFID": 1,
            "Employee ID": 1,
            "Cabins": 1,
            "Log_Cabin": 1
        }
    ))
    # Convert ObjectId to string
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify(docs)


    

@app.route('/list_cabin', methods=['GET'])
def get_cabin_list():
    docs = list(cabin_collection.find({}, {"ID": 1, "Building": 1, "Floor": 1, "Door": 1}))
    # convert ObjectId to string
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify(docs)



@app.route('/update_cabin/<id>', methods=['PUT', 'OPTIONS'])
def update_cabin(id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
    
    result = cabin_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "ID": data.get("ID"),
            "Building": data.get("Building"),
            "Floor": data.get("Floor"),
            "Door": data.get("Door")
        }}
    )
    if result.modified_count > 0:
        return jsonify({"status": "success", "message": "Record updated"})
    return jsonify({"status": "error", "message": "Record not found"}), 404


@app.route('/delete_cabin/<id>', methods=['DELETE', 'OPTIONS'])
def delete_cabin(id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    result = cabin_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count > 0:
        return jsonify({"status": "success", "message": "Record deleted"})
    return jsonify({"status": "error", "message": "Record not found"}), 404










# ---------- UPDATE ----------
@app.route('/update/<id>', methods=['PUT'])
def update_employee(id):
    try:
        print("🟡 Update endpoint hit with ID:", id)

        clean_id = id.strip().replace("'", "").replace('"', '').replace("\n", "")
        data = request.get_json()
        print("📦 Received data:", data)

        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        if not ObjectId.is_valid(clean_id):
            return jsonify({"status": "error", "message": "Invalid ObjectId"}), 400

        oid = ObjectId(clean_id)
        print("🆔 Converted ObjectId:", oid)

        # Check if document exists
        existing_doc = cabin_collection.find_one({"_id": oid})
        print("🧾 Existing Doc:", existing_doc)

        if not existing_doc:
            return jsonify({"status": "error", "message": "Record not found"}), 404

        if "_id" in data:
            del data["_id"]

        # ✅ Perform true update (no upsert)
        result = collection.update_one({"_id": oid}, {"$set": data}, upsert=False)

        print(f"Matched: {result.matched_count}, Modified: {result.modified_count}")

        if result.modified_count == 0:
            return jsonify({"status": "warning", "message": "No changes made"}), 200

        return jsonify({"status": "success", "message": "Record successfully updated"}), 200

    except Exception as e:
        import traceback
        print("❌ Error:", traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 400





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
    rfids = request.args.getlist("rfid")   # optional ?rfid=...
    date = request.args.get("date")  
    cabin_id = request.args.get("log_cabin")      # e.g. "2025-09-08"

    # --- Debug: log what we received (temporary) ---
    app.logger.debug("QUERY params - names: %s, rfids: %s, date: %s, cabin_id: %s", names, rfids, date, cabin_id)

    # --- Build filter dynamically ---
    query = {}
    if names:
        query["Name"] = {"$in": names}
    if rfids:
        query["RFID"] = {"$in": rfids}
    if date:
        query["date"] = date
    if cabin_id:
        query["Log_Cabin"] = cabin_id

    app.logger.debug("Mongo query: %s", query)

    # --- Fetch filtered logs ---
    logs = list(logs_collection.find(query, {"_id": 0}))
    app.logger.debug("Found %d logs", len(logs))
    if logs:
        app.logger.debug("Sample log: %s", logs[0])

    # --- Process logs with your function (pass original query params) ---
    result_container = {}
    thread = threading.Thread(
        target=process_all_logs,
        args=(logs, result_container, names or None, rfids or None, date or None, cabin_id or None)
    )
    thread.start()
    thread.join()

    # Always return the summary (guaranteed by process_all_logs)
    return jsonify(result_container.get("summary", [{
        "name": "",
        "rfid": "",
        "date": date or "",
        "login_time": "",
        "logout_time": "",
        "Effective_login": "",
        "Break_hours": "",
        "Total_login": "",
        "errors": "Absent",
        "log_cabin": cabin_id or ""
    }]))

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
            id = data.get("ID")
            if not rfid:
                return jsonify({"status": "error", "message": "Missing RFID field"}), 400
            if not id:
                return jsonify({"status": "error", "message": "Missing ID field"}), 400
        
            # Ensure index for fast lookup
            collection.create_index("RFID")
            #result = collection.find_one({"RFID": rfid, "Cabin": id})
            rfid_exists = collection.find_one({
            "RFID": rfid,
            "$or": [
                {"Cabins": id},
                {"Log_Cabin": id}
               ]
            })
            if rfid_exists:
                print("rfid_exists", rfid_exists)
                if id in rfid_exists.get("Cabins", []):
                    print("✅ ID found in Cabins")
                    location="Cabins"
                elif rfid_exists.get("Log_Cabin") == id:
                    print("✅ ID found in Log_Cabin")
                    location="Log_Cabin"
                else:
                    print("⚠️ ID not found in either field")
            else:
                print("❌ No document found for this RFID and ID")
                location="None"
        
            if location=="Log_Cabin":
                merged_dict={**data, **rfid_exists}
                #print("merged_dict before date and time", merged_dict)
                now_time_date = datetime.now()
                merged_dict["date"] = now_time_date.strftime("%Y-%m-%d")   # e.g. "2025-08-28"
                merged_dict["time"] = now_time_date.strftime("%H:%M:%S")   # e.g. "10:45:33"
                #print("merged_dict", merged_dict)
                thread = threading.Thread(target=create_log, args=(merged_dict,))    #creats background jobs to creat logs
                thread.start()
                #create_log(merged_dict)
        
            if not rfid_exists:
                return jsonify({
                    "status": "error",
                    "message": f"No data found for RFID {rfid}"
                }), 404   # Not Found
        
            # Convert ObjectId to string for JSON
            rfid_exists["_id"] = str(rfid_exists["_id"])
        
            return jsonify({
                "status": "success",
            }), 200
        finally:
            priority_active.clear()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
