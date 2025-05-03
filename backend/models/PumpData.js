const mongoose = require('mongoose');

const pumpDataSchema = new mongoose.Schema({
  inletFlowRate: {
    type: Number,
    required: true
  },
  outletFlowRate: {
    type: Number,
    required: true
  },
  vibration: {
    type: Number,
    required: true
  },
  temperature: {
    type: Number,
    required: true
  },
  motorVoltage: {
    type: Number,
    required: true
  },
  leakageDetected: {
    type: Boolean,
    required: true
  },
  timestamp: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('PumpData', pumpDataSchema); 