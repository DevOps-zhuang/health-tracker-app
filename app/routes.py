from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from .models import db, HealthData
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from .data_import import DataImporter
from time import time
from .utils import HealthDataHandler

# Create a Blueprint for the routes
bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    start_time = time()  # Start time for query
    entries = HealthData.query.filter_by(user_id=current_user.id).order_by(HealthData.timestamp.desc()).all()
    end_time = time()  # End time for query
    query_time = end_time - start_time
    current_app.logger.info(f'Database query time: {query_time:.4f} seconds')
    return render_template('index.html', entries=entries, user=current_user)

def validate_systolic(systolic_str):
    try:
        systolic = int(systolic_str)
        if not (100 <= systolic <= 200):
            return False, "Systolic pressure must be between 100-200"
        return True, systolic
    except:
        return False, "Systolic pressure must be a number"

def validate_diastolic(diastolic_str):
    try:
        diastolic = int(diastolic_str)
        if not (60 <= diastolic <= 160):
            return False, "Diastolic pressure must be between 60-160"
        return True, diastolic
    except:
        return False, "Diastolic pressure must be a number"

def validate_heart_rate(hr_str):
    try:
        hr = int(hr_str)
        if not (50 <= hr <= 200):
            return False, "Heart rate must be between 50-200"
        return True, hr
    except:
        return False, "Heart rate must be a number"

@bp.route('/add', methods=['POST'])
@login_required
def add_health_data():
    handler = HealthDataHandler()
    result = handler.add_entry(request.form, current_user.id)
    if result['success']:
        flash('Entry added successfully!')
    else:
        current_app.logger.error(result['message'])
        flash(result['message'])
    return redirect(url_for('main.index'))

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_health_data(id):
    entry = HealthData.query.get_or_404(id)
    if request.method == 'POST':
        handler = HealthDataHandler()
        result = handler.update_entry(id, request.form, current_user.id)
        if result['success']:
            flash('Entry updated successfully!')
            return redirect(url_for('main.index'))
        else:
            flash(result['message'])
            return redirect(url_for('main.edit_health_data', id=id))
    return render_template('edit.html', entry=entry)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_health_data(id):
    handler = HealthDataHandler()
    result = handler.delete_entry(id)
    if result['success']:
        flash('Entry deleted successfully')
    else:
        flash(result['message'])
    return redirect(url_for('main.index'))

@bp.route('/import', methods=['GET', 'POST'])
def import_data():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
            
        file = request.files['file']
        
        # Check if the file is empty
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        # Check if the file type is allowed
        allowed_extensions = {'csv', 'xlsx', 'xls', 'txt', 'jpg', 'jpeg', 'png'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            flash(f'File type not allowed. Please upload a CSV, Excel, TXT, or image file (JPG, PNG).')
            return redirect(request.url)
            
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Get import parameters
        import_format = request.form.get('format', 'auto').strip().lower()
        date_format = request.form.get('date_format', '%Y-%m-%d %H:%M:%S').strip()
        delimiter = request.form.get('delimiter', ',').strip()
        
        # Auto-detect format based on file extension if not specified
        if import_format == 'auto':
            if file_ext in ['csv']:
                import_format = 'csv'
            elif file_ext in ['xlsx', 'xls']:
                import_format = 'excel'
            elif file_ext in ['jpg', 'jpeg', 'png']:
                import_format = 'image'
            else:
                import_format = 'text'
        
        # Import based on format
        results = None
        try:
            if import_format == 'csv':
                results = DataImporter.import_from_csv(filepath, current_user.id, date_format=date_format)  # Pass user_id
            elif import_format == 'excel':
                results = DataImporter.import_from_excel(filepath)
            elif import_format == 'image':
                results = DataImporter.import_from_image(filepath)
            elif import_format == 'text':
                results = DataImporter.import_from_text(filepath, delimiter=delimiter, date_format=date_format)
            else:
                flash(f'Unsupported import format: {import_format}')
                return redirect(request.url)
                
            # Show import results
            flash(f'Import completed: {results["success"]} records imported successfully, {results["failure"]} failures')
            if results.get('duplicates', 0) > 0:
                flash(f'{results["duplicates"]} duplicate records were skipped')
            if results['failure'] > 0:
                flash(f'{results["failure"]} records failed to import')
            
            # Show errors if any
            if results['errors']:
                for error in results['errors'][:5]:  # Show only first 5 errors to avoid overwhelming the user
                    flash(f'Error: {error}')
                if len(results['errors']) > 5:
                    flash(f'...and {len(results["errors"]) - 5} more errors')
            
            # Clean up the uploaded file
            try:
                os.remove(filepath)
            except Exception as e:
                current_app.logger.warning(f"Could not remove temporary file {filepath}: {e}")
                    
            return redirect(url_for('main.index'))
            
        except Exception as e:
            flash(f'Import failed: {str(e)}')
            return redirect(request.url)
            
    # GET request - show import form
    return render_template('import.html')

@bp.route('/chart')
@login_required
def chart():
    # First get the latest record to find the end date
    latest_entry = HealthData.query.filter_by(user_id=current_user.id).order_by(HealthData.timestamp.desc()).first()
    
    if latest_entry:
        # Calculate the date range: 7 days before the latest entry
        end_date = latest_entry.timestamp
        start_date = end_date - timedelta(days=7)
        
        # Fetch health data entries within the date range, ordered by timestamp
        entries = HealthData.query.filter(
            HealthData.user_id == current_user.id,
            HealthData.timestamp >= start_date,
            HealthData.timestamp <= end_date
        ).order_by(HealthData.timestamp).all()
        
        # Debug output
        """
        print(f"Date range: {start_date} to {end_date}")
        print("Number of entries found:", len(entries))
        """

        # Format timestamps as strings that JavaScript can understand
        formatted_timestamps = [entry.timestamp.strftime('%Y-%m-%d %H:%M:%S') for entry in entries]
        systolic_values = [entry.systolic for entry in entries]
        diastolic_values = [entry.diastolic for entry in entries]
        heart_rate_values = [entry.heart_rate for entry in entries]
        
        
        # Debug output
        """
        print("Timestamps:", formatted_timestamps)
        print("Systolic values:", systolic_values)
        print("Diastolic values:", diastolic_values)
        print("Heart rate values:", heart_rate_values)
        """

        
        return render_template('chart.html', 
                            timestamps=formatted_timestamps, 
                            systolic_values=systolic_values, 
                            diastolic_values=diastolic_values,
                            heart_rate_values=heart_rate_values)
    else:
        # If no data exists, return empty arrays
        return render_template('chart.html', 
                            timestamps=[], 
                            systolic_values=[], 
                            diastolic_values=[], 
                            heart_rate_values=[])

@bp.route('/schema')
def show_schema():
    import sqlite3
    db_path = 'instance/health_tracker.sqlite'
    schema = ''
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            schema += table[0] + '\n'
        conn.close()
    except Exception as e:
        schema = f'Error: {str(e)}'
    return f'<pre>{schema}</pre>'

# Generated by Copilot