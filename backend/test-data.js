const mongoose = require('mongoose');
const SensorData = require('./models/SensorData');

// MongoDB connection
mongoose.connect('mongodb://localhost:27017/water_pump', {
  useNewUrlParser: true,
  useUnifiedTopology: true
});

// Test data
const testData = {
  flowRate: {
    inlet: 45.5,
    outlet: 44.8
  },
  voltage: {
    value: 220,
    unit: 'V'
  },
  current: {
    value: 5.2,
    unit: 'A'
  },
  power: {
    value: 1144,
    unit: 'W'
  },
  temperature: {
    value: 35.6,
    unit: '°C'
  },
  leakDetected: false,
  motorStatus: 'running'
};

// Insert test data
async function insertTestData() {
  try {
    const sensorData = new SensorData(testData);
    await sensorData.save();
    console.log('Test data inserted successfully');
    mongoose.connection.close();
  } catch (error) {
    console.error('Error inserting test data:', error);
    mongoose.connection.close();
  }
}

insertTestData(); 