const express = require('express');
const { MongoClient, ObjectId } = require('mongodb');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const PORT = 8000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// MongoDB connection
let db;
let collection;
let logsCollection;
let mongoConnected = false;

// Mock data for when MongoDB is not available
let mockUsers = [
    { _id: "1", Name: "John Doe", RFID: "123456789", "Employee ID": "EMP001" },
    { _id: "2", Name: "Jane Smith", RFID: "987654321", "Employee ID": "EMP002" }
];
let mockLogs = [];

async function connectToMongo() {
    try {
        const client = new MongoClient("mongodb://127.0.0.1:27017/");
        await client.connect();
        db = client.db("Transaction_project");
        collection = db.collection("users");
        logsCollection = db.collection("logs");
        console.log("Connected to MongoDB");
        mongoConnected = true;
        return true;
    } catch (error) {
        console.error("MongoDB connection error:", error);
        console.log("Starting server without MongoDB - some features may not work");
        return false;
    }
}

// Process logs function (converted from Python)
function processAllLogs(logs, resultContainer, queryName = null, queryRfid = null, queryDate = null) {
    // Normalize query inputs to arrays
    function toList(x) {
        if (x === null || x === undefined) {
            return [];
        }
        if (Array.isArray(x)) {
            return x;
        }
        if (typeof x === 'string' && x.includes(',')) {
            return x.split(',').map(item => item.trim()).filter(item => item);
        }
        return [x];
    }

    const qNames = toList(queryName);
    const qRfids = toList(queryRfid);
    const qDate = queryDate || "";

    // If no logs at all → return Absent rows using original query details
    if (!logs || logs.length === 0) {
        const summaries = [];
        if (qNames.length > 0 && qRfids.length > 0 && qNames.length === qRfids.length) {
            for (let i = 0; i < qNames.length; i++) {
                summaries.push({
                    name: qNames[i],
                    rfid: qRfids[i],
                    date: qDate,
                    login_time: "",
                    logout_time: "",
                    Effective_login: "",
                    Break_hours: "",
                    Total_login: "",
                    errors: "Absent"
                });
            }
        } else if (qNames.length > 0) {
            const firstRfid = qRfids.length > 0 ? qRfids[0] : "";
            for (const name of qNames) {
                summaries.push({
                    name: name,
                    rfid: firstRfid,
                    date: qDate,
                    login_time: "",
                    logout_time: "",
                    Effective_login: "",
                    Break_hours: "",
                    Total_login: "",
                    errors: "Absent"
                });
            }
        } else if (qRfids.length > 0) {
            const firstName = qNames.length > 0 ? qNames[0] : "";
            for (const rfid of qRfids) {
                summaries.push({
                    name: firstName,
                    rfid: rfid,
                    date: qDate,
                    login_time: "",
                    logout_time: "",
                    Effective_login: "",
                    Break_hours: "",
                    Total_login: "",
                    errors: "Absent"
                });
            }
        } else {
            summaries.push({
                name: "",
                rfid: "",
                date: qDate,
                login_time: "",
                logout_time: "",
                Effective_login: "",
                Break_hours: "",
                Total_login: "",
                errors: "Absent"
            });
        }

        resultContainer.summary = summaries;
        return;
    }

    // --- Normal processing when logs exist ---
    const groupedLogs = new Map();
    for (const log of logs) {
        const key = `${log.Name || ''}-${log.RFID || ''}-${log.date || ''}`;
        if (!groupedLogs.has(key)) {
            groupedLogs.set(key, []);
        }
        groupedLogs.get(key).push(log);
    }
    
    const summaries = [];
    const presentPairs = new Set();
    const presentNames = new Set();
    const presentRfids = new Set();

    for (const [key, personLogs] of groupedLogs) {
        const [name, rfid, date] = key.split('-');
        presentPairs.add(`${name}-${rfid}`);
        presentNames.add(name);
        presentRfids.add(rfid);

        // Sort logs by time
        const logsSorted = personLogs.sort((a, b) => (a.time || '').localeCompare(b.time || ''));
        
        // Add datetime property
        for (const log of logsSorted) {
            const dtStrDate = log.date || "";
            const dtStrTime = log.time || "";
            try {
                log.datetime = new Date(`${dtStrDate} ${dtStrTime}`);
            } catch (error) {
                log.datetime = null;
            }
        }
        
        let loginTime = null;
        let logoutTime = null;
        let totalLogin = 0;
        let errors = [];
        let inTime = null;
        
        for (const log of logsSorted) {
            const action = log["IN/OUT"] || "";
            const dt = log.datetime;

            if (action === "IN") {
                if (inTime === null) {
                    if (dt) {
                        inTime = dt;
                        if (loginTime === null) {
                            loginTime = inTime;
                        }
                    } else {
                        errors.push(`Bad IN datetime at ${log.time || ''}`);
                    }
                } else {
                    errors.push(`Duplicate IN at ${log.time || ''}`);
                }
            } else if (action === "OUT") {
                if (inTime !== null && dt) {
                    totalLogin += (dt - inTime) / 1000; // Convert to seconds
                    logoutTime = dt;
                    inTime = null;
                } else {
                    errors.push(`Unexpected OUT at ${log.time || ''}`);
                }
            }
        }
        
        if (inTime !== null) {
            try {
                errors.push(`Missing OUT after ${inTime.toTimeString().split(' ')[0]}`);
            } catch (error) {
                errors.push("Missing OUT after unknown time");
            }
        }
        
        let totalBreak = 0;
        let timeSpent = "";
        
        if (loginTime && logoutTime) {
            const totalDuration = (logoutTime - loginTime) / 1000; // Convert to seconds
            totalBreak = totalDuration - totalLogin;
            timeSpent = formatDuration(logoutTime - loginTime);
        }
        
        summaries.push({
            name: name,
            rfid: rfid,
            date: date,
            login_time: loginTime ? formatTime(loginTime) : "",
            logout_time: logoutTime ? formatTime(logoutTime) : "",
            Effective_login: totalLogin > 0 ? formatDuration(totalLogin * 1000) : "",
            Break_hours: totalBreak > 0 ? formatDuration(totalBreak * 1000) : "",
            Total_login: timeSpent,
            errors: errors.length > 0 ? errors : "Absent"
        });
    }

    // --- Add Absent rows for requested names/rfids that weren't present in DB result ---
    // Pairwise when lengths match
    if (qNames.length > 0 && qRfids.length > 0 && qNames.length === qRfids.length) {
        for (let i = 0; i < qNames.length; i++) {
            const pairKey = `${qNames[i]}-${qRfids[i]}`;
            if (!presentPairs.has(pairKey)) {
                summaries.push({
                    name: qNames[i],
                    rfid: qRfids[i],
                    date: qDate,
                    login_time: "",
                    logout_time: "",
                    Effective_login: "",
                    Break_hours: "",
                    Total_login: "",
                    errors: "Absent"
                });
            }
        }
    }
    // If only names requested -> add per name not present
    else if (qNames.length > 0) {
        const firstRfid = qRfids.length > 0 ? qRfids[0] : "";
        for (const name of qNames) {
            if (!presentNames.has(name)) {
                summaries.push({
                    name: name,
                    rfid: firstRfid,
                    date: qDate,
                    login_time: "",
                    logout_time: "",
                    Effective_login: "",
                    Break_hours: "",
                    Total_login: "",
                    errors: "Absent"
                });
            }
        }
    }
    // If only rfids requested -> add per rfid not present
    else if (qRfids.length > 0) {
        const firstName = qNames.length > 0 ? qNames[0] : "";
        for (const rfid of qRfids) {
            if (!presentRfids.has(rfid)) {
                summaries.push({
                    name: firstName,
                    rfid: rfid,
                    date: qDate,
                    login_time: "",
                    logout_time: "",
                    Effective_login: "",
                    Break_hours: "",
                    Total_login: "",
                    errors: "Absent"
                });
            }
        }
    }

    resultContainer.summary = summaries;
}

// Helper functions for time formatting
function formatTime(date) {
    return date.toTimeString().split(' ')[0];
}

function formatDuration(milliseconds) {
    const seconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Create log function
async function createLog(data) {
    try {
        if (data._id) {
            delete data._id; // Avoid duplicate IDs
        }
        data._id = new ObjectId();
        
        const result = await logsCollection.insertOne(data);
        console.log("Inserted document ID:", result.insertedId);
    } catch (error) {
        console.error("Error creating log:", error);
    }
}

// Routes

// Root route
app.get('/', (req, res) => {
    res.json({
        message: "Transaction Project API Server",
        status: "running",
        endpoints: {
            "POST /api/submit": "Submit RFID transaction (main endpoint)",
            "POST /submit": "Create new user",
            "GET /list": "Get all users",
            "PUT /update/:id": "Update user",
            "DELETE /delete/:id": "Delete user",
            "GET /logs": "Get transaction logs"
        },
        timestamp: new Date().toISOString()
    });
});

// Submit data
app.post('/submit', async (req, res) => {
    try {
        const data = req.body;
        if (!data) {
            return res.status(400).json({ status: "error", message: "No data received" });
        }
        
        if (mongoConnected) {
            await collection.insertOne(data);
        } else {
            const newUser = { ...data, _id: Date.now().toString() };
            mockUsers.push(newUser);
        }
        
        res.status(201).json({ status: "success", message: "Data saved" });
    } catch (error) {
        console.error("Submit error:", error);
        res.status(500).json({ status: "error", message: "Internal server error" });
    }
});

// Get list of users
app.get('/list', async (req, res) => {
    try {
        if (mongoConnected) {
            const docs = await collection.find({}, { projection: { _id: 1, Name: 1, RFID: 1, "Employee ID": 1 } }).toArray();
            
            // Convert ObjectId to string
            for (const doc of docs) {
                doc._id = doc._id.toString();
            }
            
            res.json(docs);
        } else {
            res.json(mockUsers);
        }
    } catch (error) {
        console.error("List error:", error);
        res.status(500).json({ status: "error", message: "Internal server error" });
    }
});

// Update user
app.put('/update/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const data = req.body;
        
        if (!data) {
            return res.status(400).json({ status: "error", message: "No data received" });
        }
        
        const result = await collection.updateOne(
            { _id: new ObjectId(id) },
            {
                $set: {
                    Name: data.Name,
                    RFID: data.RFID,
                    "Employee ID": data["Employee ID"]
                }
            }
        );
        
        if (result.modifiedCount > 0) {
            res.json({ status: "success", message: "Record updated" });
        } else {
            res.status(404).json({ status: "error", message: "Record not found" });
        }
    } catch (error) {
        console.error("Update error:", error);
        res.status(500).json({ status: "error", message: "Internal server error" });
    }
});

// Delete user
app.delete('/delete/:id', async (req, res) => {
    try {
        const { id } = req.params;
        
        const result = await collection.deleteOne({ _id: new ObjectId(id) });
        
        if (result.deletedCount > 0) {
            res.json({ status: "success", message: "Record deleted" });
        } else {
            res.status(404).json({ status: "error", message: "Record not found" });
        }
    } catch (error) {
        console.error("Delete error:", error);
        res.status(500).json({ status: "error", message: "Internal server error" });
    }
});

// View logs
app.get('/logs', async (req, res) => {
    try {
        if (mongoConnected) {
            const logsCollection = db.collection("logs");

            // --- Read query parameters ---
            const names = req.query.name ? (Array.isArray(req.query.name) ? req.query.name : [req.query.name]) : [];
            const rfids = req.query.rfid ? (Array.isArray(req.query.rfid) ? req.query.rfid : [req.query.rfid]) : [];
            const date = req.query.date || null;

            // --- Debug: log what we received (temporary) ---
            console.log("QUERY params - names:", names, "rfids:", rfids, "date:", date);

            // --- Build filter dynamically ---
            const query = {};
            if (names.length > 0) {
                query["Name"] = { $in: names };
            }
            if (rfids.length > 0) {
                query["RFID"] = { $in: rfids };
            }
            if (date) {
                query["date"] = date;
            }

            console.log("Mongo query:", query);

            // --- Fetch filtered logs ---
            const logs = await logsCollection.find(query, { projection: { _id: 0 } }).toArray();
            console.log("Found", logs.length, "logs");
            if (logs.length > 0) {
                console.log("Sample log:", logs[0]);
            }

            // --- Process logs with your function (pass original query params) ---
            const resultContainer = {};
            processAllLogs(logs, resultContainer, names.length > 0 ? names : null, rfids.length > 0 ? rfids : null, date);

            // Always return the summary (guaranteed by processAllLogs)
            res.json(resultContainer.summary || [{
                name: "",
                rfid: "",
                date: date || "",
                login_time: "",
                logout_time: "",
                Effective_login: "",
                Break_hours: "",
                Total_login: "",
                errors: "Absent"
            }]);
        } else {
            res.json(mockLogs);
        }
    } catch (error) {
        console.error("Logs error:", error);
        res.status(500).json({ status: "error", message: "Internal server error" });
    }
});

// API submit endpoint
app.post('/api/submit', async (req, res) => {
    try {
        // Check if content type is JSON (Express doesn't have req.is method)
        const contentType = req.headers['content-type'];
        if (!contentType || !contentType.includes('application/json')) {
            return res.status(400).json({ 
                status: "error", 
                message: "Content-Type must be application/json" 
            });
        }
        
        const data = req.body;
        console.log(data);
        
        if (!data) {
            return res.status(400).json({ 
                status: "error", 
                message: "Invalid or empty JSON" 
            });
        }
        
        const rfid = data.RFID;
        if (!rfid) {
            return res.status(400).json({ 
                status: "error", 
                message: "Missing RFID field" 
            });
        }
        
        let result;
        
        if (mongoConnected) {
            // Ensure index for fast lookup
            await collection.createIndex("RFID");
            result = await collection.findOne({ RFID: rfid });
        } else {
            result = mockUsers.find(user => user.RFID === rfid);
        }
        
        if (result) {
            const mergedDict = { ...data, ...result };
            const nowTimeDate = new Date();
            mergedDict.date = nowTimeDate.toISOString().split('T')[0]; // YYYY-MM-DD
            mergedDict.time = nowTimeDate.toTimeString().split(' ')[0]; // HH:MM:SS
            console.log(mergedDict);
            
            // Create log in background
            if (mongoConnected) {
                createLog(mergedDict);
            } else {
                mockLogs.push({ ...mergedDict, _id: Date.now().toString() });
            }
        }
        
        if (!result) {
            return res.status(404).json({
                status: "error",
                message: `No data found for RFID ${rfid}`
            });
        }
        
        // Convert ObjectId to string for JSON
        result._id = result._id.toString();
        
        res.status(200).json({
            status: "success"
        });
    } catch (error) {
        console.error("API submit error:", error);
        res.status(500).json({ status: "error", message: "Internal server error" });
    }
});

// Start server
async function startServer() {
    try {
        const mongoConnected = await connectToMongo();
        app.listen(PORT, '0.0.0.0', () => {
            console.log(`Server is running on http://0.0.0.0:${PORT}`);
            if (mongoConnected) {
                console.log('✅ MongoDB connected successfully');
            } else {
                console.log('⚠️  MongoDB not available - using mock data');
            }
        });
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}

startServer();
