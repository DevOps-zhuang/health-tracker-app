import csv
import pandas as pd
from datetime import datetime
from flask import current_app
from .models import HealthData, db

class DataImporter:
    """Utility class for importing health data from various formats."""
    
    @staticmethod
    def validate_data(systolic, diastolic, heart_rate):
        """
        Validate the blood pressure and heart rate values.
        
        Args:
            systolic (int): Systolic blood pressure value
            diastolic (int): Diastolic blood pressure value
            heart_rate (int): Heart rate value
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Validate systolic pressure
        if not isinstance(systolic, (int, float)) or not (100 <= systolic <= 200):
            return False, f"Invalid systolic value: {systolic}. Must be between 100-200."
            
        # Validate diastolic pressure
        if not isinstance(diastolic, (int, float)) or not (60 <= diastolic <= 160):
            return False, f"Invalid diastolic value: {diastolic}. Must be between 60-160."
            
        # Validate relationship between systolic and diastolic
        if systolic <= diastolic:
            return False, f"Systolic ({systolic}) must be greater than diastolic ({diastolic})."
            
        # Validate heart rate
        if not isinstance(heart_rate, (int, float)) or not (50 <= heart_rate <= 200):
            return False, f"Invalid heart rate value: {heart_rate}. Must be between 50-200."
            
        return True, ""

    @classmethod
    def import_from_csv(cls, file_path, date_format='%Y-%m-%d %H:%M:%S'):
        """
        Import health data from a CSV file.
        
        Args:
            file_path (str): Path to the CSV file
            date_format (str): Format of the date/time in the CSV
            
        Returns:
            dict: Import results with counts of success, failures, and errors
        """
        results = {
            'success': 0,
            'failure': 0,
            'errors': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                # Try to detect if the file has headers
                first_line = csvfile.readline().strip()
                csvfile.seek(0)  # Reset file pointer
                
                has_headers = '测量时间' in first_line or 'timestamp' in first_line.lower()
                reader = csv.reader(csvfile)
                
                if has_headers:
                    next(reader)  # Skip header row
                
                for row in reader:
                    try:
                        if len(row) < 4:
                            results['failure'] += 1
                            results['errors'].append(f"Row has insufficient values: {row}")
                            continue
                            
                        # Skip rows with placeholder values
                        if '--' in row:
                            results['failure'] += 1
                            results['errors'].append(f"Row contains placeholder values: {row}")
                            continue
                        
                        # Parse values from the row (timestamp, systolic, diastolic, heart_rate)
                        timestamp_str = row[0].strip()
                        systolic = int(float(row[1]))
                        diastolic = int(float(row[2]))
                        heart_rate = int(float(row[3]))
                        
                        # Validate data
                        is_valid, error_msg = cls.validate_data(systolic, diastolic, heart_rate)
                        if not is_valid:
                            results['failure'] += 1
                            results['errors'].append(f"Row validation failed: {error_msg}")
                            continue
                        
                        # Parse timestamp
                        try:
                            timestamp = datetime.strptime(timestamp_str, date_format)
                        except ValueError:
                            results['failure'] += 1
                            results['errors'].append(f"Invalid timestamp format: {timestamp_str}")
                            continue
                        
                        # Create new health data entry
                        new_entry = HealthData(
                            systolic=systolic,
                            diastolic=diastolic,
                            heart_rate=heart_rate,
                            timestamp=timestamp
                        )
                        
                        # Add to database
                        db.session.add(new_entry)
                        results['success'] += 1
                    
                    except Exception as e:
                        results['failure'] += 1
                        results['errors'].append(f"Error processing row: {str(e)}")
                
                # Commit all valid entries
                if results['success'] > 0:
                    db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            results['errors'].append(f"Fatal error during import: {str(e)}")
        
        return results

    @classmethod
    def import_from_excel(cls, file_path, sheet_name=0, date_format=None):
        """
        Import health data from an Excel file.
        
        Args:
            file_path (str): Path to the Excel file
            sheet_name (str/int): Name or index of the sheet to import
            date_format (str): Format of the date/time (if needed to override pandas defaults)
            
        Returns:
            dict: Import results with counts of success, failures, and errors
        """
        results = {
            'success': 0,
            'failure': 0,
            'errors': []
        }
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Check required columns
            required_columns = ['timestamp', 'systolic', 'diastolic', 'heart_rate']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                results['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
                return results
            
            # Process each row
            for _, row in df.iterrows():
                try:
                    # Extract values
                    timestamp = row['timestamp']
                    systolic = int(row['systolic'])
                    diastolic = int(row['diastolic'])
                    heart_rate = int(row['heart_rate'])
                    tags = row.get('tags', '')
                    
                    # Validate data
                    is_valid, error_msg = cls.validate_data(systolic, diastolic, heart_rate)
                    if not is_valid:
                        results['failure'] += 1
                        results['errors'].append(f"Row validation failed: {error_msg}")
                        continue
                    
                    # Ensure timestamp is datetime
                    if not isinstance(timestamp, (datetime, pd.Timestamp)):
                        results['failure'] += 1
                        results['errors'].append(f"Invalid timestamp format: {timestamp}")
                        continue
                    
                    # Convert pandas timestamp to datetime if needed
                    if isinstance(timestamp, pd.Timestamp):
                        timestamp = timestamp.to_pydatetime()
                    
                    # Create new health data entry
                    new_entry = HealthData(
                        systolic=systolic,
                        diastolic=diastolic,
                        heart_rate=heart_rate,
                        tags=str(tags) if not pd.isna(tags) else "",
                        timestamp=timestamp
                    )
                    
                    # Add to database
                    db.session.add(new_entry)
                    results['success'] += 1
                
                except Exception as e:
                    results['failure'] += 1
                    results['errors'].append(f"Error processing row: {str(e)}")
            
            # Commit all valid entries
            if results['success'] > 0:
                db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            results['errors'].append(f"Fatal error during import: {str(e)}")
        
        return results
    
    @classmethod 
    def import_from_text(cls, file_path, delimiter=',', date_format='%Y-%m-%d %H:%M:%S'):
        """
        Import health data from a custom text file format.
        
        Args:
            file_path (str): Path to the text file
            delimiter (str): Delimiter used in the file (default: comma)
            date_format (str): Format of the date/time in the file
            
        Returns:
            dict: Import results with counts of success, failures, and errors
        """
        results = {
            'success': 0,
            'failure': 0,
            'errors': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Read header
                header = file.readline().strip().split(delimiter)
                
                # Check if header contains required fields
                required_fields = ['timestamp', 'systolic', 'diastolic', 'heart_rate']
                if not all(field in header for field in required_fields):
                    results['errors'].append(f"Missing required fields in header. Expected: {', '.join(required_fields)}")
                    return results
                
                # Create field indices
                field_indices = {field: header.index(field) for field in header}
                
                # Process data rows
                for line_num, line in enumerate(file, start=2):  # Start from 2 to account for header
                    try:
                        values = line.strip().split(delimiter)
                        if len(values) < len(header):
                            results['failure'] += 1
                            results['errors'].append(f"Line {line_num}: Insufficient values")
                            continue
                        
                        # Extract values using field indices
                        timestamp_str = values[field_indices['timestamp']]
                        systolic = int(float(values[field_indices['systolic']]))
                        diastolic = int(float(values[field_indices['diastolic']]))
                        heart_rate = int(float(values[field_indices['heart_rate']]))
                        
                        # Extract tags if present
                        tags = values[field_indices['tags']] if 'tags' in field_indices else ''
                        
                        # Validate data
                        is_valid, error_msg = cls.validate_data(systolic, diastolic, heart_rate)
                        if not is_valid:
                            results['failure'] += 1
                            results['errors'].append(f"Line {line_num}: {error_msg}")
                            continue
                        
                        # Parse timestamp
                        try:
                            timestamp = datetime.strptime(timestamp_str, date_format)
                        except ValueError:
                            results['failure'] += 1
                            results['errors'].append(f"Line {line_num}: Invalid timestamp format: {timestamp_str}")
                            continue
                        
                        # Create new health data entry
                        new_entry = HealthData(
                            systolic=systolic,
                            diastolic=diastolic,
                            heart_rate=heart_rate,
                            tags=tags,
                            timestamp=timestamp
                        )
                        
                        # Add to database
                        db.session.add(new_entry)
                        results['success'] += 1
                    
                    except Exception as e:
                        results['failure'] += 1
                        results['errors'].append(f"Line {line_num}: {str(e)}")
                
                # Commit all valid entries
                if results['success'] > 0:
                    db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            results['errors'].append(f"Fatal error during import: {str(e)}")
        
        return results

    @classmethod
    def import_from_image(cls, file_path):
        """
        Import health data from an image file.
        This is a placeholder for future implementation using OpenAI services.
        
        Args:
            file_path (str): Path to the image file
            
        Returns:
            dict: Import results with counts of success, failures, and errors
        """
        results = {
            'success': 0,
            'failure': 0,
            'errors': ['Image import feature is not yet implemented. Will be supported using OpenAI services in the future.']
        }
        return results

# Generated by Copilot

import csv
from datetime import datetime

data = [
    ["测量时间", "高压(mmHg)", "低压(mmHg)", "心率(bpm)"],
    ["2025-03-04 07:45:00", 127, 83, 65],
    ["2025-03-04 18:20:00", 132, 90, 66],
    ["2025-03-03 07:35:00", 129, 83, 66],
    ["2025-03-03 19:20:00", 121, 79, 63],
    ["2025-03-03 11:57:00", 122, 83, 60],
    ["2025-03-03 16:31:00", 136, 83, 61],
    ["2025-03-02 21:20:00", 140, 94, 65],
    ["2025-03-02 20:28:00", 130, 89, 67],
    ["2025-03-01 23:31:00", 133, 92, 65],
    ["2025-03-02 08:16:00", 134, 93, 66],
    ["2025-03-02 10:45:00", 121, 77, 60],
    ["2025-03-02 20:43:00", 133, 86, 71],
    ["2025-03-02 23:13:00", 125, 83, 65],
    ["2025-03-01 09:00:00", 144, 93, 68],
    ["2025-03-01 22:56:00", 131, 87, 65],
    ["2025-02-28 07:42:00", 136, 87, 73],
    ["2025-02-28 20:47:00", 120, 77, 73],
    ["2025-02-28 23:33:00", 113, 74, 66],
    ["2025-02-27 21:12:00", 135, 88, 60],
    ["2025-02-27 21:13:00", 136, 96, 63],
    ["2025-02-26 07:32:00", 138, 94, 67],
    ["2025-02-26 13:03:00", 130, 86, 60],
    ["2025-02-26 20:15:00", 137, 91, 64],
    ["2025-02-26 20:16:00", 134, 91, 63],
    ["2025-02-25 00:06:00", 121, 83, 62],
    ["2025-02-25 07:40:00", 141, 101, 68],
    ["2025-02-25 22:03:00", 126, 83, 62],
    ["2025-02-25 23:38:00", 131, 85, 61],
    ["2025-02-24 08:01:00", 125, 85, 64],
    ["2025-02-24 19:44:00", 136, 88, 64],
    ["2025-02-23 07:28:00", 126, 81, 68],
    ["2025-02-23 11:13:00", 111, 78, 64],
    ["2025-02-23 11:59:00", 124, 84, 66],
    ["2025-02-23 22:02:00", 131, 81, 62],
    ["2025-02-22 00:00:00", "--", "--", "--"],
    ["2025-02-21 07:28:00", 143, 95, 62],
    ["2025-02-21 15:30:00", 150, 101, 65],
    ["2025-02-21 21:33:00", 134, 92, 62],
    ["2025-02-20 07:41:00", 146, 92, 57],
    ["2025-02-20 10:50:00", 134, 89, 59],
    ["2025-02-20 13:57:00", 149, 100, 58],
    ["2025-02-20 15:22:00", 149, 97, 58],
    ["2025-02-20 17:26:00", 164, 97, 57],
    ["2025-02-20 20:33:00", 136, 89, 60],
    ["2025-02-19 09:46:00", 135, 88, 69],
    ["2025-02-19 12:38:00", 158, 94, 57],
    ["2025-02-19 17:20:00", 152, 104, 55],
    ["2025-02-19 21:14:00", 133, 84, 58]
]

# Write CSV with UTF-8 BOM
with open('exports/health_data_20250304.csv', 'w', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)
    writer.writerows(data)