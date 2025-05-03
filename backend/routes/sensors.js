const express = require('express');
const router = express.Router();
const PumpData = require('../models/PumpData');
const mqtt = require('mqtt');

// Function to log with separator
function logWithSeparator(message) {
  console.log('\n---------------------------------------');
  console.log(message);
  console.log('---------------------------------------\n');
}

// Initialize MQTT client
const mqttClient = mqtt.connect('mqtt://192.168.79.206:1883');

// Store latest readings
let latestReadings = {
  inletFlowRate: 0,
  outletFlowRate: 0,
  vibration: 0,
  temperature: 0,
  motorVoltage: 0,
  leakageDetected: false,
  timestamp: new Date()
};

// Subscribe to MQTT topics
mqttClient.on('connect', () => {
  logWithSeparator('Connected to MQTT broker');
  mqttClient.subscribe('pump/data', (err) => {
    if (!err) {
      logWithSeparator('Subscribed to pump/data topic');
    }
  });
});

// Handle incoming MQTT messages
mqttClient.on('message', async (topic, message) => {
  if (topic === 'pump/data') {
    try {
      const data = JSON.parse(message.toString());
      
      // Create new pump data record
      const pumpData = new PumpData({
        inletFlowRate: data.inletFlowRate,
        outletFlowRate: data.outletFlowRate,
        vibration: data.vibration,
        temperature: data.temperature,
        motorVoltage: data.motorVoltage,
        leakageDetected: data.leakageDetected,
        timestamp: new Date()
      });

      await pumpData.save();
      logWithSeparator('New Data Received:' + 
        '\nInlet Flow: ' + data.inletFlowRate.toFixed(2) + ' L/min' +
        '\nOutlet Flow: ' + data.outletFlowRate.toFixed(2) + ' L/min' +
        '\nVibration: ' + data.vibration.toFixed(2) +
        '\nTemperature: ' + data.temperature.toFixed(2) + '°C' +
        '\nMotor Voltage: ' + data.motorVoltage.toFixed(2) + 'V' +
        '\nLeakage Status: ' + (data.leakageDetected ? 'DETECTED!' : 'Normal')
      );

      // Update latest readings
      latestReadings = {
        ...data,
        timestamp: new Date()
      };
      
    } catch (error) {
      logWithSeparator('Error saving data: ' + error);
    }
  }
});

// API Routes
router.get('/latest', async (req, res) => {
  try {
    const data = await PumpData.findOne().sort({ timestamp: -1 });
    if (data) {
      res.json(data);
    } else {
      res.json(latestReadings);
    }
  } catch (error) {
    logWithSeparator('Error fetching latest data: ' + error);
    res.status(500).json({ error: 'Error fetching latest data' });
  }
});

router.get('/historical', async (req, res) => {
  try {
    const data = await PumpData.find()
      .sort({ timestamp: -1 })
      .limit(100);
    res.json(data);
  } catch (error) {
    logWithSeparator('Error fetching historical data: ' + error);
    res.status(500).json({ error: 'Error fetching historical data' });
  }
});

router.get('/leaks', async (req, res) => {
  try {
    const leaks = await PumpData.find({ leakageDetected: true })
      .sort({ timestamp: -1 })
      .limit(50);
    res.json(leaks);
  } catch (error) {
    logWithSeparator('Error fetching leak data: ' + error);
    res.status(500).json({ error: 'Error fetching leak data' });
  }
});

// New route for motor control
router.post('/control', (req, res) => {
  try {
    const { motor_state, reason } = req.body;
    
    if (!motor_state || !['on', 'off'].includes(motor_state)) {
      return res.status(400).json({ error: 'Invalid motor state' });
    }

    // Publish command to MQTT
    const command = {
      command: motor_state,
      reason: reason || 'Manual control'
    };

    mqttClient.publish('pump/control', JSON.stringify(command), (err) => {
      if (err) {
        logWithSeparator('Error publishing command: ' + err);
        return res.status(500).json({ error: 'Failed to send command' });
      }
      logWithSeparator(`Motor control command sent: ${motor_state.toUpperCase()}\nReason: ${command.reason}`);
      res.json({ message: 'Command sent successfully' });
    });
  } catch (error) {
    logWithSeparator('Error in motor control: ' + error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;