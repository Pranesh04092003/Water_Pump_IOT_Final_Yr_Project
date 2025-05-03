import serial
import pandas as pd
import numpy as np
from datetime import datetime
import time
import os
import serial.tools.list_ports

class MPU6050DataCollector:
    def __init__(self, port='COM3', baud_rate=9600):
        """
        Initialize the data collector for MPU6050
        Args:
            port: Serial port where Arduino is connected (default COM3)
            baud_rate: Communication speed (default 9600 for Arduino)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        self.data = []
    
    def check_port_availability(self):
        """Check if COM3 is available"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.device == 'COM3':
                print(f"\nFound COM3: {port.description}")
                return True
        print("\nCOM3 not found in available ports!")
        return False
    
    def connect(self):
        """Establish connection with Arduino"""
        if not self.check_port_availability():
            print("\nTroubleshooting steps:")
            print("1. Make sure Arduino is connected to USB")
            print("2. Check if Arduino is showing up in Device Manager")
            print("3. Try unplugging and replugging the Arduino")
            print("4. Try a different USB port")
            return False
        
        try:
            # Try to close any existing connection
            if self.serial and self.serial.is_open:
                self.serial.close()
            
            print(f"\nTrying to connect to {self.port}...")
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Wait for Arduino to initialize
            time.sleep(2)
            
            # Clear any existing data in the buffer
            while self.serial.in_waiting:
                self.serial.readline()
            
            print(f"✅ Successfully connected to Arduino on {self.port}")
            return True
            
        except serial.SerialException as e:
            print(f"\n❌ Error connecting to {self.port}:")
            print(f"Error details: {str(e)}")
            print("\nTroubleshooting tips:")
            print("1. Make sure no other program is using COM3")
            print("2. Try closing Arduino IDE if it's open")
            print("3. Check if the correct drivers are installed")
            print("4. Try restarting your computer")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            return False
    
    def read_vibration(self):
        """Read averaged vibration data from Arduino"""
        try:
            if self.serial.in_waiting:
                # Read the line from serial port
                line = self.serial.readline().decode('utf-8').strip()
                # Parse the data (format: "vibration,temperature,voltage")
                # We only use the vibration value (first value)
                vibration = float(line.split(',')[0])
                return vibration
            return None
        except Exception as e:
            print(f"❌ Error reading vibration data: {str(e)}")
            return None
    
    def collect_vibration_data(self, total_readings=2000, reading_interval=0.1):
        """
        Collect vibration data
        Args:
            total_readings: Total number of readings to collect
            reading_interval: Time between readings in seconds
        """
        if not self.serial:
            print("❌ Not connected to Arduino")
            return None
        
        vibration_data = []
        start_time = time.time()
        last_progress_time = time.time()
        
        print(f"\nStarting vibration data collection...")
        print(f"Target: {total_readings} readings")
        print("Press Ctrl+C to stop collection")
        print("\nProgress:")
        
        try:
            while len(vibration_data) < total_readings:
                vibration = self.read_vibration()
                if vibration is not None:
                    timestamp = datetime.now()
                    vibration_data.append({
                        'timestamp': timestamp,
                        'vibration': vibration,
                        'time_elapsed': time.time() - start_time
                    })
                    
                    # Show progress every second
                    current_time = time.time()
                    if current_time - last_progress_time >= 1.0:
                        progress = (len(vibration_data) / total_readings) * 100
                        print(f"\rProgress: {len(vibration_data)}/{total_readings} ({progress:.1f}%) - Current vibration: {vibration:.2f} g", end="")
                        last_progress_time = current_time
                
                time.sleep(reading_interval)
            
            print("\n\n✅ Data collection completed!")
            return vibration_data
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Data collection interrupted by user")
            return vibration_data
        except Exception as e:
            print(f"\n\n❌ Error during data collection: {str(e)}")
            return vibration_data
    
    def save_data(self, data, filename='mpu6050_vibration_data.csv'):
        """Save collected data to CSV file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Convert data to DataFrame
            df = pd.DataFrame(data)
            
            # Save to CSV
            filepath = os.path.join('data', filename)
            df.to_csv(filepath, index=False)
            print(f"✅ Data saved to {filepath}")
            
            # Print data statistics
            print("\nData Statistics:")
            print(f"Total readings: {len(data)}")
            print(f"Average vibration: {df['vibration'].mean():.2f} g")
            print(f"Maximum vibration: {df['vibration'].max():.2f} g")
            print(f"Minimum vibration: {df['vibration'].min():.2f} g")
            print(f"Standard deviation: {df['vibration'].std():.2f} g")
            
        except Exception as e:
            print(f"❌ Error saving data: {str(e)}")
    
    def close(self):
        """Close the serial connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("✅ Serial connection closed")

def main():
    # Initialize collector with COM3
    collector = MPU6050DataCollector(port='COM3')
    
    # Connect to Arduino
    if not collector.connect():
        return
    
    try:
        # Collect vibration data
        print("\nStarting vibration data collection...")
        print("Please ensure the motor is running and the MPU6050 is properly mounted.")
        print("You can test different motor conditions (normal, overheating, failure)")
        print("Press Ctrl+C to stop collection at any time\n")
        
        vibration_data = collector.collect_vibration_data(
            total_readings=2000,  # Collect 2000 readings
            reading_interval=0.1   # 100ms between readings
        )
        
        if vibration_data:
            # Save the collected data
            collector.save_data(vibration_data, 'mpu6050_vibration_data.csv')
    
    finally:
        collector.close()

if __name__ == "__main__":
    main() 