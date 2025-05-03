const express = require('express');
const mongoose = require('mongoose');
const mqtt = require('mqtt');
const cors = require('cors');
const path = require('path');
const WebSocket = require('ws');
const http = require('http');

// Function to log with separator
function logWithSeparator(message) {
  console.log('\n---------------------------------------');
  console.log(message);
  console.log('---------------------------------------\n');
}

const app = express();
app.use(cors());
app.use(express.json());

// Create HTTP server
const server = http.createServer(app);

// Create WebSocket server
const wss = new WebSocket.Server({ server });

// Store connected WebSocket clients
const clients = new Set();

// WebSocket connection handler
wss.on('connection', (ws) => {
  clients.add(ws);
  logWithSeparator('New client connected');

  ws.on('close', () => {
    clients.delete(ws);
    logWithSeparator('Client disconnected');
  });
});

// Broadcast data to all connected clients
function broadcastData(data) {
  clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(data));
    }
  });
}

// MongoDB Connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/water-pump');

const db = mongoose.connection;
db.on('error', console.error.bind(console, 'MongoDB connection error:'));
db.once('open', () => logWithSeparator('Connected to MongoDB'));

// MQTT Client Setup
const mqttClient = mqtt.connect('mqtt://192.168.79.206:1883');

mqttClient.on('connect', () => {
  logWithSeparator('Connected to MQTT broker');
  mqttClient.subscribe('pump/data', (err) => {
    if (!err) {
      logWithSeparator('Subscribed to pump/data topic');
    }
  });
});

mqttClient.on('message', async (topic, message) => {
  if (topic === 'pump/data') {
    try {
      const data = JSON.parse(message.toString());
      // Broadcast the data to all connected WebSocket clients
      broadcastData(data);
      logWithSeparator('Data broadcasted to WebSocket clients');
    } catch (error) {
      logWithSeparator('Error processing MQTT message: ' + error);
    }
  }
});

// Routes
const sensorRoutes = require('./routes/sensors');
app.use('/api/sensors', sensorRoutes);

const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  logWithSeparator('Server running on port ' + PORT);
});
