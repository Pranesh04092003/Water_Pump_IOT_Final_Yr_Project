import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
import seaborn as sns
from datetime import datetime, timedelta

def generate_sample_data(n_samples=1000):
    # Generate time points
    time = np.linspace(0, 10, n_samples)
    
    # Generate raw vibration signal with noise
    fundamental_freq = 50  # Hz
    raw_signal = np.sin(2 * np.pi * fundamental_freq * time)
    noise = np.random.normal(0, 0.5, n_samples)
    raw_signal_with_noise = raw_signal + noise
    
    # Apply Butterworth filter
    b, a = signal.butter(4, 0.1, 'low')
    filtered_signal = signal.filtfilt(b, a, raw_signal_with_noise)
    
    return time, raw_signal_with_noise, filtered_signal

def calculate_vibration_features(signal_data):
    rms = np.sqrt(np.mean(np.square(signal_data)))
    peak = np.max(np.abs(signal_data))
    crest_factor = peak / rms
    return rms, peak, crest_factor

def plot_combined_analysis():
    # Create plots directory if it doesn't exist
    import os
    os.makedirs('plots', exist_ok=True)
    
    # Set figure parameters for academic publication
    plt.rcParams.update({
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'figure.titlesize': 14,
        'figure.figsize': (10, 8),
        'figure.dpi': 300,
        'axes.grid': True,
        'grid.linestyle': '--',
        'grid.alpha': 0.7
    })
    
    # Generate sample data
    time, raw_signal, filtered_signal = generate_sample_data()
    
    # Create a figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1)
    fig.suptitle('Vibration Analysis for Condition Monitoring', y=0.95)
    
    # Plot 1: Raw vs Filtered Data
    ax1.plot(time, raw_signal, label='Raw Signal', alpha=0.5, color='#1f77b4')
    ax1.plot(time, filtered_signal, label='Filtered Signal', linewidth=2, color='#ff7f0e')
    ax1.set_title('(a) Raw vs. Filtered Vibration Data')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amplitude')
    ax1.legend(loc='upper right', framealpha=0.9)
    
    # Calculate features for different time windows
    window_size = 100
    n_windows = len(raw_signal) // window_size
    
    rms_values = []
    peak_values = []
    crest_factors = []
    time_points = []
    
    for i in range(n_windows):
        start_idx = i * window_size
        end_idx = (i + 1) * window_size
        window_data = filtered_signal[start_idx:end_idx]
        
        rms, peak, crest = calculate_vibration_features(window_data)
        rms_values.append(rms)
        peak_values.append(peak)
        crest_factors.append(crest)
        time_points.append(time[start_idx])
    
    # Plot 2: Vibration Features
    ax2.plot(time_points, rms_values, label='RMS', marker='o', markersize=4, color='#2ca02c')
    ax2.plot(time_points, peak_values, label='Peak', marker='s', markersize=4, color='#d62728')
    ax2.plot(time_points, crest_factors, label='Crest Factor', marker='^', markersize=4, color='#9467bd')
    ax2.set_title('(b) Extracted Vibration Features')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Value')
    ax2.legend(loc='upper right', framealpha=0.9)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the figure with high resolution
    plt.savefig('plots/combined_vibration_analysis.png', bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    plot_combined_analysis()
