import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def determine_condition(vibration):
    """
    Determine motor condition based on vibration levels (in g-force)
    Thresholds based on collected MPU6050 data
    """
    if vibration < 2.0:  # Less than 2g is normal
        return 0  # Normal
    elif vibration < 3.0:  # Between 2g and 3g is overheating
        return 1  # Overheating
    else:  # More than 3g indicates failure
        return 2  # Failure

def determine_cooling_efficiency(vibration_reduction, condition):
    """
    Determine cooling efficiency based on vibration reduction and condition
    Thresholds adjusted for MPU6050 accelerometer data
    """
    if condition == 2:  # Failure
        return False
    elif condition == 1:  # Overheating
        return vibration_reduction > 0.25  # 25% reduction required
    else:  # Normal
        return vibration_reduction > 0.3  # 30% reduction required

def prepare_cooling_data(data):
    """Prepare cooling model features from vibration data"""
    # Calculate rolling statistics
    window_size = 10  # 10 readings window
    data['peak_vibration'] = data['vibration'].rolling(window=window_size).max()
    data['stable_vibration'] = data['vibration'].rolling(window=window_size).mean()
    
    # Calculate cooling duration (time between peaks)
    data['cooling_duration'] = data['time_elapsed'].diff()
    
    # Calculate vibration reduction
    data['vibration_reduction'] = (data['peak_vibration'] - data['stable_vibration']) / data['peak_vibration']
    
    # Calculate average vibration
    data['avg_vibration'] = data['vibration'].rolling(window=window_size).mean()
    
    # Drop rows with NaN values
    data = data.dropna()
    
    return data

def train_models():
    """Train both vibration and cooling efficiency models using MPU6050 data"""
    # Load MPU6050 data
    try:
        data = pd.read_csv('data/mpu6050_vibration_data.csv')
        print("✅ Successfully loaded MPU6050 vibration data")
    except Exception as e:
        print(f"❌ Error loading MPU6050 data: {str(e)}")
        return
    
    # Prepare cooling data
    cooling_data = prepare_cooling_data(data.copy())
    
    # Prepare features for vibration model
    X_vibration = data[['vibration']].values
    y_vibration = data['vibration'].apply(determine_condition).values
    
    # Prepare features for cooling model
    cooling_features = ['vibration', 'peak_vibration', 'stable_vibration', 
                       'cooling_duration', 'vibration_reduction', 'avg_vibration']
    X_cooling = cooling_data[cooling_features].values
    y_cooling = np.array([
        determine_cooling_efficiency(row['vibration_reduction'], 
                                   determine_condition(row['vibration']))
        for _, row in cooling_data.iterrows()
    ]).astype(int)
    
    # Split data for both models
    X_vib_train, X_vib_test, y_vib_train, y_vib_test = train_test_split(
        X_vibration, y_vibration, test_size=0.2, random_state=42
    )
    
    X_cool_train, X_cool_test, y_cool_train, y_cool_test = train_test_split(
        X_cooling, y_cooling, test_size=0.2, random_state=42
    )
    
    # Train vibration model
    vibration_model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )
    vibration_model.fit(X_vib_train, y_vib_train)
    
    # Train cooling efficiency model
    cooling_model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )
    cooling_model.fit(X_cool_train, y_cool_train)
    
    # Evaluate vibration model
    vib_predictions = vibration_model.predict(X_vib_test)
    vib_accuracy = accuracy_score(y_vib_test, vib_predictions)
    print("\nVibration Model Performance:")
    print(f"Accuracy: {vib_accuracy:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_vib_test, vib_predictions, 
          target_names=['Normal', 'Overheating', 'Failure']))
    
    # Evaluate cooling model
    cool_predictions = cooling_model.predict(X_cool_test)
    cool_accuracy = accuracy_score(y_cool_test, cool_predictions)
    print("\nCooling Efficiency Model Performance:")
    print(f"Accuracy: {cool_accuracy:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_cool_test, cool_predictions,
          target_names=['Inefficient', 'Efficient']))
    
    # Save models
    os.makedirs('models', exist_ok=True)
    joblib.dump(vibration_model, 'models/vibration_model.joblib')
    joblib.dump(cooling_model, 'models/cooling_model.joblib')
    
    # Save feature names for reference
    with open('models/cooling_features.txt', 'w') as f:
        f.write('\n'.join(cooling_features))
    
    print("\nModels trained and saved successfully!")
    return vibration_model, cooling_model

if __name__ == "__main__":
    train_models()
