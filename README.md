# Transaction Project - Node.js Version

This is a Node.js conversion of the original Python Flask application for managing RFID-based transaction logs.

## Features

- **User Management**: CRUD operations for users with RFID tags
- **Transaction Logging**: Automatic logging of IN/OUT transactions
- **Log Analysis**: Process and analyze transaction logs with time calculations
- **RESTful API**: Complete API endpoints for all operations

## Prerequisites

- Node.js (v14 or higher)
- MongoDB (running on localhost:27017)
- npm or yarn package manager

## Installation

1. Install dependencies:
```bash
npm install
```

2. Make sure MongoDB is running on your system:
```bash
# Start MongoDB (if not already running)
mongod
```

## Running the Application

### Development Mode (with auto-restart)
```bash
npm run dev
```

### Production Mode
```bash
npm start
```

The server will start on `http://0.0.0.0:8000`

## API Endpoints

### User Management
- `POST /submit` - Create a new user
- `GET /list` - Get all users
- `PUT /update/:id` - Update a user
- `DELETE /delete/:id` - Delete a user

### Transaction Logging
- `POST /api/submit` - Submit RFID transaction (main endpoint)
- `GET /logs` - Get processed transaction logs

## Database Structure

The application uses MongoDB with two collections:
- `users` - Stores user information (Name, RFID, Employee ID)
- `logs` - Stores transaction logs with timestamps

## Example Usage

### Submit a transaction
```bash
curl -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"RFID": "123456789"}'
```

### Get all users
```bash
curl http://localhost:8000/list
```

### Get transaction logs
```bash
curl http://localhost:8000/logs
```

## Conversion Notes

This Node.js version maintains the same functionality as the original Python Flask application:

- Same API endpoints and response formats
- Same MongoDB database structure
- Same transaction processing logic
- Same time calculation algorithms
- CORS enabled for cross-origin requests

The main differences are:
- Uses Express.js instead of Flask
- Async/await pattern for database operations
- JavaScript date handling instead of Python datetime
- Node.js threading model (background processing handled differently)
