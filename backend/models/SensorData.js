const mongoose = require('mongoose');

const sensorDataSchema = new mongoose.Schema({
  timestamp: {
    type: Date,
    default: Date.now
  },
  flowRate: {
    inlet: { type: Number, required: true },
    outlet: { type: Number, required: true }
  },
  vibration: { type: Number, required: true },
  temperature: { type: Number, required: true },
  motorVoltage: { type: Number, required: true },
  leakDetected: {
    type: Boolean,
    default: false
  },
  motorStatus: {
    type: String,
    enum: ['running', 'stopped', 'fault'],
    default: 'stopped'
  }
});

// Add a method to round numbers to 6 decimal places
sensorDataSchema.pre('save', function(next) {
  // Round flowRate values
  if (this.flowRate) {
    this.flowRate.inlet = Number(this.flowRate.inlet.toFixed(6));
    this.flowRate.outlet = Number(this.flowRate.outlet.toFixed(6));
  }
  
  // Round other sensor values
  if (this.vibration) this.vibration = Number(this.vibration.toFixed(6));
  if (this.temperature) this.temperature = Number(this.temperature.toFixed(6));
  if (this.motorVoltage) this.motorVoltage = Number(this.motorVoltage.toFixed(6));
  
  next();
});

// Index for efficient time-series queries
sensorDataSchema.index({ timestamp: -1 });

module.exports = mongoose.model('SensorData', sensorDataSchema);
