const express = require('express');
const router = express.Router();
const mqtt = require('mqtt');

const mqttClient = mqtt.connect(process.env.MQTT_BROKER_URL || 'mqtt://localhost:1883');

// Store latest motor and sensor readings
let latestMotorData = {
  voltage: 0,
  current: 0,
  temperature: 0,
  vibration: 0,
  efficiency: 0,
  isRunning: false,
  speed: 0,
  runtime: 0,
  flowRate: {
    inlet: 0,
    outlet: 0
  },
  leakDetected: false,
  faultStatus: null,
  lastUpdate: null
};

// Subscribe to ESP32 sensor topics
mqttClient.on('connect', () => {
  const topics = [
    'pump/flow/inlet',
    'pump/flow/outlet',
    'pump/vibration',
    'pump/temperature',
    'pump/voltage',
    'pump/leak_status',
    'pump/status'
  ];
  
  topics.forEach(topic => {
    mqttClient.subscribe(topic, (err) => {
      if (err) console.error('MQTT subscription error:', err);
    });
  });
});

// Handle incoming MQTT messages from ESP32
mqttClient.on('message', (topic, message) => {
  const value = message.toString();
  latestMotorData.lastUpdate = new Date();

  switch (topic) {
    case 'pump/flow/inlet':
      latestMotorData.flowRate.inlet = parseFloat(value);
      break;
    case 'pump/flow/outlet':
      latestMotorData.flowRate.outlet = parseFloat(value);
      break;
    case 'pump/vibration':
      latestMotorData.vibration = parseFloat(value);
      break;
    case 'pump/temperature':
      latestMotorData.temperature = parseFloat(value);
      break;
    case 'pump/voltage':
      latestMotorData.voltage = parseFloat(value);
      break;
    case 'pump/leak_status':
      latestMotorData.leakDetected = value === 'true';
      break;
    case 'pump/status':
      latestMotorData.isRunning = value === 'true';
      break;
  }
  
  // Calculate efficiency based on current operating parameters
  latestMotorData.efficiency = calculateEfficiency(latestMotorData);
});

// Calculate motor efficiency including flow parameters
function calculateEfficiency(data) {
  // Enhanced efficiency calculation including flow rates
  const nominalVoltage = 220;
  const maxTemp = 80;
  const maxVibration = 10;
  
  const voltageEfficiency = (1 - Math.abs(data.voltage - nominalVoltage) / nominalVoltage) * 100;
  const tempEfficiency = (1 - data.temperature / maxTemp) * 100;
  const vibrationEfficiency = (1 - data.vibration / maxVibration) * 100;
  const flowEfficiency = data.flowRate.outlet > 0 ? 
    (data.flowRate.outlet / data.flowRate.inlet) * 100 : 0;
  
  return (voltageEfficiency + tempEfficiency + vibrationEfficiency + flowEfficiency) / 4;
}

// Get motor status
router.get('/status', async (req, res) => {
  try {
    // Check if data is stale (no updates in last 5 seconds)
    const isStale = latestMotorData.lastUpdate && 
      (new Date() - latestMotorData.lastUpdate) > 5000;

    res.json({
      ...latestMotorData,
      isStale
    });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

// Start motor
router.post('/start', async (req, res) => {
  try {
    mqttClient.publish('pump/command', JSON.stringify({ 
      action: 'start',
      relay: 'HIGH'  // Adjust based on your relay logic
    }));
    res.json({ message: 'Start command sent successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

// Stop motor
router.post('/stop', async (req, res) => {
  try {
    mqttClient.publish('pump/command', JSON.stringify({ 
      action: 'stop',
      relay: 'LOW'  // Adjust based on your relay logic
    }));
    res.json({ message: 'Stop command sent successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

// Get fault history
router.get('/faults', async (req, res) => {
  try {
    const faults = [];
    if (latestMotorData.leakDetected) {
      faults.push({
        id: Date.now(),
        timestamp: new Date(),
        type: 'leak',
        description: 'Water leak detected between inlet and outlet'
      });
    }
    if (latestMotorData.temperature > 80) {
      faults.push({
        id: Date.now() + 1,
        timestamp: new Date(),
        type: 'overtemp',
        description: 'Motor temperature exceeded safe limits'
      });
    }
    if (latestMotorData.vibration > 10) {
      faults.push({
        id: Date.now() + 2,
        timestamp: new Date(),
        type: 'vibration',
        description: 'Excessive vibration detected'
      });
    }
    res.json(faults);
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

module.exports = router;
