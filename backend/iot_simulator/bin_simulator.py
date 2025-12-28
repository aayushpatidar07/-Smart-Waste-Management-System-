"""
============================================
Smart Waste Management System
IoT Bin Sensor Simulator
============================================
Simulates smart bin sensors that:
- Generate random waste level data
- Update database with sensor readings
- Simulate real-time IoT behavior
- Can run continuously or for testing
============================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Bin, Database
import random
import time
from datetime import datetime
import schedule


class BinSensorSimulator:
    """
    Simulates IoT sensors in smart waste bins
    Generates realistic waste level data
    """
    
    def __init__(self):
        self.bin_model = Bin()
        self.db = Database()
    
    def generate_sensor_reading(self, current_level, bin_type='general'):
        """
        Generate realistic sensor reading
        Args:
            current_level: Current waste level (%)
            bin_type: Type of bin (general, recyclable, organic, hazardous)
        Returns: New waste level (%)
        """
        # Different fill rates for different bin types
        fill_rates = {
            'general': (1.5, 4.0),      # 1.5-4% increase per reading
            'recyclable': (0.8, 2.5),   # Slower fill rate
            'organic': (2.0, 5.0),      # Faster fill rate
            'hazardous': (0.3, 1.0)     # Very slow fill rate
        }
        
        min_increase, max_increase = fill_rates.get(bin_type, (1.0, 3.0))
        
        # Random increase in waste level
        increase = random.uniform(min_increase, max_increase)
        
        # Small chance of decrease (waste compression or removal)
        if random.random() < 0.05:  # 5% chance
            increase = -random.uniform(0.5, 2.0)
        
        new_level = current_level + increase
        
        # Ensure level stays within bounds
        new_level = max(0, min(100, new_level))
        
        return round(new_level, 2)
    
    def generate_temperature(self):
        """Generate realistic temperature reading (Celsius)"""
        # Temperature between 20-35°C
        base_temp = 27.0
        variation = random.uniform(-3.0, 5.0)
        return round(base_temp + variation, 2)
    
    def generate_humidity(self):
        """Generate realistic humidity reading (%)"""
        # Humidity between 40-80%
        base_humidity = 60.0
        variation = random.uniform(-15.0, 15.0)
        return round(base_humidity + variation, 2)
    
    def determine_sensor_status(self, waste_level, temperature, humidity):
        """
        Determine sensor status based on readings
        Returns: normal, warning, or error
        """
        if waste_level >= 95:
            return 'error'  # Overfull - sensor issue
        elif waste_level >= 85 or temperature > 32:
            return 'warning'
        else:
            return 'normal'
    
    def update_bin_sensor(self, bin_id):
        """
        Update sensor reading for a specific bin
        Args:
            bin_id: Bin ID to update
        """
        # Get current bin data
        bin_data = self.bin_model.get_bin_by_id(bin_id)
        
        if not bin_data or bin_data['status'] != 'active':
            return
        
        current_level = float(bin_data['waste_level'])
        bin_type = bin_data['bin_type']
        
        # Generate new readings
        new_level = self.generate_sensor_reading(current_level, bin_type)
        temperature = self.generate_temperature()
        humidity = self.generate_humidity()
        sensor_status = self.determine_sensor_status(new_level, temperature, humidity)
        
        # Update bin waste level
        self.bin_model.update_waste_level(bin_id, new_level)
        
        # Insert sensor log
        query = """
            INSERT INTO sensor_logs 
            (bin_id, waste_level, temperature, humidity, sensor_status)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.db.execute_query(
            query,
            (bin_id, new_level, temperature, humidity, sensor_status),
            fetch=False
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Updated {bin_data['bin_code']}: "
              f"{new_level}% (was {current_level}%) | Temp: {temperature}°C | "
              f"Humidity: {humidity}% | Status: {sensor_status}")
    
    def update_all_bins(self):
        """Update sensor readings for all active bins"""
        print("\n" + "=" * 70)
        print(f"IoT Sensor Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Get all active bins
        bins = self.bin_model.get_all_bins()
        
        for bin_data in bins:
            if bin_data['status'] == 'active':
                self.update_bin_sensor(bin_data['bin_id'])
        
        print("=" * 70)
        print("Sensor update completed!\n")
    
    def simulate_collection(self, bin_id, vehicle_id=None):
        """
        Simulate waste collection - reset bin level
        Args:
            bin_id: Bin ID to collect from
            vehicle_id: Vehicle performing collection
        """
        bin_data = self.bin_model.get_bin_by_id(bin_id)
        
        if not bin_data:
            return
        
        before_level = float(bin_data['waste_level'])
        
        # After collection, bin has small residual waste (2-8%)
        after_level = random.uniform(2.0, 8.0)
        
        # Update bin level
        self.bin_model.update_waste_level(bin_id, after_level)
        
        # Log collection
        query = """
            INSERT INTO collection_logs 
            (bin_id, vehicle_id, collected_by, waste_amount, before_level, after_level)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        waste_amount = (before_level - after_level) * float(bin_data['capacity']) / 100
        
        self.db.execute_query(
            query,
            (bin_id, vehicle_id, None, waste_amount, before_level, after_level),
            fetch=False
        )
        
        print(f"[COLLECTION] {bin_data['bin_code']}: Collected {before_level}% -> {after_level}%")
    
    def run_continuous(self, update_interval_minutes=5):
        """
        Run simulator continuously
        Args:
            update_interval_minutes: How often to update sensors
        """
        print("=" * 70)
        print("Smart Waste Management - IoT Sensor Simulator")
        print("=" * 70)
        print(f"Update Interval: Every {update_interval_minutes} minutes")
        print("Press Ctrl+C to stop")
        print("=" * 70)
        
        # Schedule updates
        schedule.every(update_interval_minutes).minutes.do(self.update_all_bins)
        
        # Run first update immediately
        self.update_all_bins()
        
        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nSimulator stopped by user")
            print("=" * 70)
    
    def run_single_update(self):
        """Run a single update cycle for all bins"""
        self.update_all_bins()


# =============================================
# COMMAND LINE INTERFACE
# =============================================

def main():
    """Main function for CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Waste Bin IoT Sensor Simulator')
    parser.add_argument(
        '--mode',
        choices=['continuous', 'single', 'collect'],
        default='single',
        help='Simulation mode: continuous (runs forever), single (one update), collect (simulate collection)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Update interval in minutes (for continuous mode)'
    )
    parser.add_argument(
        '--bin-id',
        type=int,
        help='Specific bin ID (for collect mode)'
    )
    
    args = parser.parse_args()
    
    simulator = BinSensorSimulator()
    
    if args.mode == 'continuous':
        simulator.run_continuous(update_interval_minutes=args.interval)
    
    elif args.mode == 'single':
        simulator.run_single_update()
    
    elif args.mode == 'collect':
        if args.bin_id:
            simulator.simulate_collection(args.bin_id)
        else:
            # Collect from all full bins (>= 80%)
            bin_model = Bin()
            full_bins = bin_model.get_full_bins(threshold=80)
            
            print("=" * 70)
            print("Simulating Collection from Full Bins")
            print("=" * 70)
            
            for bin_data in full_bins:
                simulator.simulate_collection(bin_data['bin_id'], vehicle_id=1)
            
            print("=" * 70)


if __name__ == '__main__':
    main()
