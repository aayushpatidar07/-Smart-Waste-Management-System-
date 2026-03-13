"""
============================================
Smart Waste Management System
IoT Bin Sensor Simulator
============================================
Simulates smart bin sensors that:
- Generate random waste level data
- Update database with sensor readings
- Simulate real-time IoT behavior
- Auto-create waste logs on threshold crossings
- Generate alerts for critical bins
- Can run continuously or for testing
============================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Bin, Database
from waste_log import WasteLog
import random
import time
from datetime import datetime
import schedule


class BinSensorSimulator:
    """
    Simulates IoT sensors in smart waste bins
    Generates realistic waste level data
    """

    # Thresholds for auto-logging and alerts
    ALERT_CRITICAL_THRESHOLD = 85
    ALERT_WARNING_THRESHOLD = 70
    AUTO_LOG_THRESHOLD = 75  # Automatically create waste log when bin exceeds this

    def __init__(self):
        self.bin_model = Bin()
        self.db = Database()
        self._logged_bins = set()  # Track bins that got auto-logged this cycle

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
        base_temp = 27.0
        variation = random.uniform(-3.0, 5.0)
        return round(base_temp + variation, 2)

    def generate_humidity(self):
        """Generate realistic humidity reading (%)"""
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

    def create_auto_waste_log(self, bin_id, fill_level, reason='sensor'):
        """
        Automatically create a waste log entry when threshold is crossed.
        Args:
            bin_id (int): Bin ID
            fill_level (float): Current fill level
            reason (str): Note about why log was created
        """
        notes = f"Auto-logged by IoT sensor ({reason}). Fill level: {fill_level}%"
        result = WasteLog.create_waste_log(bin_id, fill_level, notes)
        if result.get('success'):
            print(f"  → Auto-waste-log created for bin {bin_id} [{fill_level}%]")
        return result

    def create_alert(self, bin_id, bin_code, alert_type, message, severity):
        """
        Create an alert record in the database.
        Args:
            bin_id (int): Bin ID
            bin_code (str): Bin code for display
            alert_type (str): Type of alert
            message (str): Alert message
            severity (str): info | warning | critical
        """
        query = """
            INSERT INTO alerts (bin_id, alert_type, message, severity, status)
            VALUES (%s, %s, %s, %s, 'active')
        """
        self.db.execute_query(query, (bin_id, alert_type, message, severity), fetch=False)
        print(f"  ⚠ Alert [{severity.upper()}] for {bin_code}: {message}")

    def update_bin_sensor(self, bin_id):
        """
        Update sensor reading for a specific bin and handle thresholds.
        Args:
            bin_id: Bin ID to update
        """
        bin_data = self.bin_model.get_bin_by_id(bin_id)

        if not bin_data or bin_data['status'] != 'active':
            return

        current_level = float(bin_data['waste_level'])
        bin_type = bin_data['bin_type']
        bin_code = bin_data['bin_code']

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

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Updated {bin_code}: "
              f"{new_level}% (was {current_level}%) | Temp: {temperature}°C | "
              f"Humidity: {humidity}% | Status: {sensor_status}")

        # Auto-create waste log if threshold crossed
        if new_level >= self.AUTO_LOG_THRESHOLD and bin_id not in self._logged_bins:
            self.create_auto_waste_log(bin_id, new_level, reason='threshold_crossed')
            self._logged_bins.add(bin_id)

        # Generate alert for critical / warning levels
        if new_level >= self.ALERT_CRITICAL_THRESHOLD:
            self.create_alert(
                bin_id, bin_code,
                alert_type='high_fill_level',
                message=f'Bin {bin_code} is {new_level}% full – immediate collection needed',
                severity='critical'
            )
        elif new_level >= self.ALERT_WARNING_THRESHOLD and current_level < self.ALERT_WARNING_THRESHOLD:
            # Only create warning alert when first crossing threshold
            self.create_alert(
                bin_id, bin_code,
                alert_type='high_fill_level',
                message=f'Bin {bin_code} has reached {new_level}% fill level',
                severity='warning'
            )

    def update_all_bins(self):
        """Update sensor readings for all active bins"""
        print("\n" + "=" * 70)
        print(f"IoT Sensor Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        self._logged_bins.clear()  # Reset auto-log tracker each cycle

        # Get all active bins
        bins = self.bin_model.get_all_bins()
        updated = 0

        for bin_data in bins:
            if bin_data['status'] == 'active':
                self.update_bin_sensor(bin_data['bin_id'])
                updated += 1

        print("=" * 70)
        print(f"Sensor update completed! {updated} bins updated.\n")

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

        # Create waste log for the collection event
        self.create_auto_waste_log(
            bin_id, after_level,
            reason=f'post_collection (was {before_level}%)'
        )

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

    def get_simulation_summary(self):
        """
        Print a summary report of current bin statuses.
        """
        bins = self.bin_model.get_all_bins()
        critical = [b for b in bins if float(b.get('waste_level', 0)) >= 85]
        warning  = [b for b in bins if 70 <= float(b.get('waste_level', 0)) < 85]
        normal   = [b for b in bins if float(b.get('waste_level', 0)) < 70]

        print("\n" + "=" * 70)
        print("SIMULATION SUMMARY")
        print("=" * 70)
        print(f"Total Bins  : {len(bins)}")
        print(f"Critical (≥85%): {len(critical)}")
        print(f"Warning  (70-84%): {len(warning)}")
        print(f"Normal   (<70%) : {len(normal)}")

        if critical:
            print("\nCritical Bins:")
            for b in critical:
                print(f"  • {b['bin_code']} [{b['location']}] – {b['waste_level']}%")
        print("=" * 70 + "\n")

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
        print(f"Auto-log threshold: {self.AUTO_LOG_THRESHOLD}%")
        print(f"Critical alert threshold: {self.ALERT_CRITICAL_THRESHOLD}%")
        print("Press Ctrl+C to stop")
        print("=" * 70)

        # Schedule updates
        schedule.every(update_interval_minutes).minutes.do(self.update_all_bins)

        # Run first update immediately
        self.update_all_bins()
        self.get_simulation_summary()

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nSimulator stopped by user")
            self.get_simulation_summary()
            print("=" * 70)

    def run_single_update(self):
        """Run a single update cycle for all bins"""
        self.update_all_bins()
        self.get_simulation_summary()


# =============================================
# COMMAND LINE INTERFACE
# =============================================

def main():
    """Main function for CLI"""
    import argparse

    parser = argparse.ArgumentParser(description='Smart Waste Bin IoT Sensor Simulator')
    parser.add_argument(
        '--mode',
        choices=['continuous', 'single', 'collect', 'summary'],
        default='single',
        help='Simulation mode: continuous (runs forever), single (one update), '
             'collect (simulate collection), summary (print bin statuses)'
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
    parser.add_argument(
        '--threshold',
        type=int,
        default=80,
        help='Fill level threshold for collect mode (default: 80)'
    )

    args = parser.parse_args()

    simulator = BinSensorSimulator()

    if args.mode == 'continuous':
        simulator.run_continuous(update_interval_minutes=args.interval)

    elif args.mode == 'single':
        simulator.run_single_update()

    elif args.mode == 'summary':
        simulator.get_simulation_summary()

    elif args.mode == 'collect':
        if args.bin_id:
            simulator.simulate_collection(args.bin_id)
        else:
            # Collect from all full bins
            bin_model = Bin()
            full_bins = bin_model.get_full_bins(threshold=args.threshold)

            print("=" * 70)
            print(f"Simulating Collection from Bins ≥ {args.threshold}%")
            print("=" * 70)

            for bin_data in full_bins:
                simulator.simulate_collection(bin_data['bin_id'], vehicle_id=1)

            print("=" * 70)


if __name__ == '__main__':
    main()



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
