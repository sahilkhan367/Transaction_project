from pymongo import MongoClient
from datetime import datetime, timedelta

# Connect to local MongoDB (default port 27017)
client = MongoClient("mongodb://localhost:27017/")

# Select database
db = client["Transaction_project"]

# Select collection
collection = db["logs"]
log_list=[]
# Read all documents
documents = collection.find().sort([
    ("date", 1),
    ("Name",1)
])


from datetime import datetime
from collections import defaultdict

def process_all_logs(logs):
    """
    Process logs for multiple people, grouped by Name, RFID, and date.
    Returns a dictionary with summaries.
    """
    
    # Group logs by (Name, RFID, Date)
    grouped_logs = defaultdict(list)
    for log in logs:
        grouped_logs[(log["Name"], log["RFID"], log["date"])].append(log)
    
    summaries = {}
    
    # Process each group
    for (name, rfid, date), person_logs in grouped_logs.items():
        # Sort logs by time
        logs_sorted = sorted(person_logs, key=lambda x: x["time"])
        
        # Parse times
        for log in logs_sorted:
            log["datetime"] = datetime.strptime(f'{log["date"]} {log["time"]}', "%Y-%m-%d %H:%M:%S")
        
        # Initialize
        login_time, logout_time = None, None
        total_login, errors, last_action, in_time = 0, [], None, None
        
        # Process IN/OUT sequence
        for log in logs_sorted:
            action = log["IN/OUT"]
            
            if action == "IN":
                if last_action == "IN":
                    errors.append(f"Transaction Error at {log['time']}: consecutive IN")
                else:
                    if login_time is None:
                        login_time = log["datetime"]
                    in_time = log["datetime"]
            
            elif action == "OUT":
                if last_action == "OUT":
                    errors.append(f"Transaction Error at {log['time']}: consecutive OUT")
                else:
                    if in_time:
                        total_login += (log["datetime"] - in_time).total_seconds()
                    logout_time = log["datetime"]
                    in_time = None
            
            last_action = action
        
        # Calculate break time
        total_break = 0
        if login_time and logout_time:
            total_duration = (logout_time - login_time).total_seconds()
            total_break = total_duration - total_login
        
        # Save summary
        summaries[(name, rfid, date)] = {
            "login_time": login_time.strftime("%H:%M:%S") if login_time else None,
            "logout_time": logout_time.strftime("%H:%M:%S") if logout_time else None,
            "total_login_hours": str(timedelta(seconds=total_login)),
            "total_break_hours": str(timedelta(seconds=total_break)),
            "errors": errors
        }
    
    return summaries









print("Data in testCollection:")
for doc in documents:
    print(doc)
    log_list.append(doc)
print(log_list)
summary = process_all_logs(log_list)
for key, val in summary.items():
    print(key, "=>", val)