import csv
import pandas as pd
import datetime
from flask import current_app, flash
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
        
        Expected CSV format:
        timestamp,systolic,diastolic,heart_rate,tags
        2023-01-01 12:00:00,120,80,75,morning
        
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
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        # Parse values from the row
                        timestamp_str = row.get('timestamp', '').strip()
                        systolic = int(float(row.get('systolic', 0)))
                        diastolic = int(float(row.get('diastolic', 0)))
                        heart_rate = int(float(row.get('heart_rate', 0)))
                        tags = row.get('tags', '').strip()
                        
                        # Validate data
                        is_valid, error_msg = cls.validate_data(systolic, diastolic, heart_rate)
                        if not is_valid:
                            results['failure'] += 1
                            results['errors'].append(f"Row validation failed: {error_msg}")
                            continue
                        
                        # Parse timestamp
                        try:
                            timestamp = datetime.datetime.strptime(timestamp_str, date_format)
                        except ValueError:
                            results['failure'] += 1
                            results['errors'].append(f"Invalid timestamp format: {timestamp_str}")
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
                        results['errors'].append(f"Error processing row: {str(e)}")
                
                # Commit all valid entries
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
                    if not isinstance(timestamp, (datetime.datetime, pd.Timestamp)):
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
                            timestamp = datetime.datetime.strptime(timestamp_str, date_format)
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
                db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            results['errors'].append(f"Fatal error during import: {str(e)}")
        
        return results

# Generated by Copilot