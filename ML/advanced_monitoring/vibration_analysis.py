import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, confusion_matrix
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import xgboost as xgb
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

class VibrationAnalysis:
    def __init__(self):
        # Generate sample vibration data
        self.timestamps = pd.date_range(start='2025-01-01', periods=1000, freq='H')
        self.vibration_data = self.generate_vibration_data()
        
    def generate_vibration_data(self):
        # Simulate normal vibration with occasional anomalies
        base_vibration = np.sin(np.linspace(0, 100, 1000)) * 0.5
        noise = np.random.normal(0, 0.1, 1000)
        trend = np.linspace(0, 0.5, 1000)
        
        # Add some anomalies
        anomalies = np.zeros(1000)
        anomaly_indices = np.random.choice(1000, 50, replace=False)
        anomalies[anomaly_indices] = np.random.uniform(1, 2, 50)
        
        return base_vibration + noise + trend + anomalies
    
    def prepare_lstm_data(self, sequence_length=50):
        # Prepare data for LSTM
        X, y = [], []
        for i in range(len(self.vibration_data) - sequence_length):
            X.append(self.vibration_data[i:i + sequence_length])
            y.append(self.vibration_data[i + sequence_length])
        return np.array(X), np.array(y)
    
    def train_lstm_model(self):
        # Prepare data
        X, y = self.prepare_lstm_data()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        # Create and train LSTM model
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(50, 1)),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.fit(X_train.reshape(-1, 50, 1), y_train, epochs=10, batch_size=32, verbose=0)
        
        # Make predictions
        predictions = model.predict(X_test.reshape(-1, 50, 1)).flatten()
        return y_test, predictions
    
    def plot_time_series(self):
        # Plot time series with predictions
        y_test, predictions = self.train_lstm_model()
        
        plt.figure(figsize=(12, 6))
        plt.plot(self.timestamps[-len(y_test):], y_test, label='Actual', alpha=0.7)
        plt.plot(self.timestamps[-len(predictions):], predictions, label='Predicted', alpha=0.7)
        plt.title('Time-Series Analysis: Vibration Fluctuations with LSTM Predictions')
        plt.xlabel('Time')
        plt.ylabel('Vibration Amplitude')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('plots/vibration_time_series.png')
        plt.close()

class CoolingEfficiencyAnalysis:
    def __init__(self):
        # Generate sample cooling efficiency data
        self.n_samples = 1000
        self.X, self.y = self.generate_cooling_data()
        
    def generate_cooling_data(self):
        # Generate synthetic features for cooling system
        temperature = np.random.normal(60, 15, self.n_samples)
        pressure = np.random.normal(100, 20, self.n_samples)
        flow_rate = np.random.normal(50, 10, self.n_samples)
        
        # Create feature matrix
        X = np.column_stack([temperature, pressure, flow_rate])
        
        # Generate target variable (efficiency classification)
        y = (temperature * 0.3 + pressure * 0.4 + flow_rate * 0.3 + 
             np.random.normal(0, 10, self.n_samples)) > np.mean(temperature + pressure + flow_rate)
        return X, y.astype(int)
    
    def train_xgboost_model(self):
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(self.X, self.y, test_size=0.2)
        
        # Train XGBoost model
        model = xgb.XGBClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Get predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        return y_test, y_pred, y_pred_proba
    
    def plot_results(self):
        y_test, y_pred, y_pred_proba = self.train_xgboost_model()
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1)
        ax1.set_title('Confusion Matrix')
        ax1.set_xlabel('Predicted')
        ax1.set_ylabel('Actual')
        
        # Plot ROC curve
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        roc_auc = auc(fpr, tpr)
        
        ax2.plot(fpr, tpr, color='darkorange', lw=2, 
                label=f'ROC curve (AUC = {roc_auc:.2f})')
        ax2.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        ax2.set_xlim([0.0, 1.0])
        ax2.set_ylim([0.0, 1.05])
        ax2.set_xlabel('False Positive Rate')
        ax2.set_ylabel('True Positive Rate')
        ax2.set_title('Receiver Operating Characteristic')
        ax2.legend(loc="lower right")
        
        plt.tight_layout()
        plt.savefig('plots/cooling_efficiency_results.png')
        plt.close()

def main():
    # Create plots directory if it doesn't exist
    import os
    if not os.path.exists('plots'):
        os.makedirs('plots')
    
    # Generate Time-Series Analysis
    print("Generating vibration time-series analysis...")
    vib_analysis = VibrationAnalysis()
    vib_analysis.plot_time_series()
    
    # Generate Cooling Efficiency Results
    print("Generating cooling efficiency analysis...")
    cool_analysis = CoolingEfficiencyAnalysis()
    cool_analysis.plot_results()
    
    print("Analysis complete! Plots have been saved in the 'plots' directory.")

if __name__ == "__main__":
    main()
