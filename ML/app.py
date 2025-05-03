from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import joblib
import numpy as np
from datetime import datetime
import os
from pymongo import MongoClient
from bson import json_util
import json
import requests

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['water-pump']
collection = db['pumpdatas']

# Node.js server URL
NODE_SERVER_URL = 'http://localhost:5000/api/sensors'

# Load models
vibration_model = joblib.load('models/vibration_model.joblib')
cooling_model = joblib.load('models/cooling_model.joblib')

# Load cooling features
with open('models/cooling_features.txt', 'r') as f:
    cooling_features = f.read().splitlines()

# Initialize history and previous status
vibration_history = []
cooling_history = []
status_counts = {'Normal': 0, 'Overheating': 0, 'Failure': 0}
cooling_counts = {'Efficient': 0, 'Inefficient': 0}
previous_status = None  # Track previous status

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/get_latest_data')
def get_latest_data():
    try:
        global previous_status  # Use global to track status changes
        
        # Get the latest 10 records from MongoDB
        latest_records = list(collection.find().sort('timestamp', -1).limit(10))
        
        if not latest_records:
            return jsonify({
                'status': 'No Data',
                'cooling_status': 'No Data',
                'vibration': 0,
                'health_score': 100,
                'cooling_metrics': {
                    'duration': 0,
                    'reduction': 0,
                    'stable_vibration': 0
                },
                'history': {
                    'vibration': [],
                    'cooling': []
                },
                'counts': {
                    'status': {'Normal': 0, 'Overheating': 0, 'Failure': 0},
                    'cooling': {'Efficient': 0, 'Inefficient': 0}
                }
            })
        
        # Convert ObjectId to string for JSON serialization
        for record in latest_records:
            record['_id'] = str(record['_id'])
            record['timestamp'] = record['timestamp'].isoformat()
        
        # Extract vibration data
        vibration_data = [{'time': record['timestamp'], 'value': record['vibration']} 
                         for record in latest_records]
        
        # Get the latest vibration value
        latest_vibration = latest_records[0]['vibration'] if latest_records else 0
        
        # Make predictions
        vibration_pred = int(vibration_model.predict([[latest_vibration]])[0])
        
        # Simulate cooling cycle data
        peak_vibration = latest_vibration * 1.1
        stable_vibration = latest_vibration * 0.7
        cooling_duration = np.random.uniform(15, 30)
        vibration_reduction = (peak_vibration - stable_vibration) / peak_vibration
        avg_vibration = (peak_vibration + stable_vibration) / 2
        
        # Make cooling prediction
        cooling_features_values = [[latest_vibration, peak_vibration, stable_vibration,
                                  cooling_duration, vibration_reduction, avg_vibration]]
        cooling_pred = bool(cooling_model.predict(cooling_features_values)[0])
        
        # Convert predictions to labels
        status_map = {0: 'Normal', 1: 'Overheating', 2: 'Failure'}
        status = status_map[vibration_pred]
        
        # Handle motor control based on status changes
        try:
            if status == 'Failure':
                print(f"Sending motor control command for Failure state. Vibration: {latest_vibration}")
                response = requests.post(f'{NODE_SERVER_URL}/control', json={
                    'motor_state': 'off',
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'ML model predicted Failure state'
                })
                if response.status_code != 200:
                    print(f"Failed to send motor control command: {response.text}")
                else:
                    print("Successfully sent motor control command")
            
            # If previous status was Failure and current status is not Failure
            elif previous_status == 'Failure' and status != 'Failure':
                print(f"Sending motor control command to turn ON. Previous: {previous_status}, Current: {status}")
                response = requests.post(f'{NODE_SERVER_URL}/control', json={
                    'motor_state': 'on',
                    'timestamp': datetime.now().isoformat(),
                    'reason': f'Status changed from Failure to {status}'
                })
                if response.status_code != 200:
                    print(f"Failed to send motor control command: {response.text}")
                else:
                    print("Successfully sent motor control command")
            
            # Update previous status
            previous_status = status
            
        except Exception as e:
            print(f"Error sending motor control command: {str(e)}")
        
        # Determine cooling efficiency
        cooling_status = 'Efficient'
        if vibration_reduction < 0.25:
            cooling_status = 'Inefficient'
        elif status == 'Overheating' and vibration_reduction < 0.3:
            cooling_status = 'Inefficient'
        elif status == 'Failure':
            cooling_status = 'Inefficient'
        
        # Update counts
        status_counts[status] += 1
        cooling_counts[cooling_status] += 1
        
        # Calculate health score
        health_score = max(0, min(100, 100 - (latest_vibration / 4.0 * 100)))
        
        return jsonify({
            'status': status,
            'cooling_status': cooling_status,
            'vibration': latest_vibration,
            'health_score': round(health_score, 1),
            'cooling_metrics': {
                'duration': round(cooling_duration, 1),
                'reduction': round(vibration_reduction * 100, 1),
                'stable_vibration': round(stable_vibration, 1)
            },
            'history': {
                'vibration': vibration_data,
                'cooling': cooling_history[-3:]
            },
            'counts': {
                'status': status_counts,
                'cooling': cooling_counts
            }
        })
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'Error',
            'cooling_status': 'Error',
            'vibration': 0,
            'health_score': 0,
            'cooling_metrics': {
                'duration': 0,
                'reduction': 0,
                'stable_vibration': 0
            },
            'history': {
                'vibration': [],
                'cooling': []
            },
            'counts': {
                'status': {'Normal': 0, 'Overheating': 0, 'Failure': 0},
                'cooling': {'Efficient': 0, 'Inefficient': 0}
            }
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
