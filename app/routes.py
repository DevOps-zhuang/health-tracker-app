from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from .models import db, HealthData
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from .data_import import DataImporter

# Create a Blueprint for the routes
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Fetch all health data entries from the database, ordered by timestamp
    entries = HealthData.query.order_by(HealthData.timestamp.desc()).all()
    return render_template('index.html', entries=entries)

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
def add_health_data():
    systolic = request.form.get('systolic')
    diastolic = request.form.get('diastolic')
    heart_rate = request.form.get('heart_rate')
    tags = request.form.get('tags')
    timestamp_str = request.form.get('timestamp')

    # Validate systolic pressure
    sys_valid, sys_result = validate_systolic(systolic)
    if not sys_valid:
        flash(sys_result)
        return redirect(url_for('main.index'))
    systolic_value = sys_result

    # Validate diastolic pressure
    dias_valid, dias_result = validate_diastolic(diastolic)
    if not dias_valid:
        flash(dias_result)
        return redirect(url_for('main.index'))
    diastolic_value = dias_result

    # Ensure systolic is greater than diastolic
    if systolic_value <= diastolic_value:
        flash("Systolic pressure must be greater than diastolic pressure")
        return redirect(url_for('main.index'))

    # Validate heart rate
    hr_valid, hr_result = validate_heart_rate(heart_rate)
    if not hr_valid:
        flash(hr_result)
        return redirect(url_for('main.index'))
    heart_rate_value = hr_result

    # Process timestamp
    if timestamp_str:
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash("Invalid date format")
            return redirect(url_for('main.index'))
    else:
        timestamp = datetime.utcnow()

    # Create a new health data entry
    new_entry = HealthData(
        systolic=systolic_value,
        diastolic=diastolic_value,
        heart_rate=heart_rate_value,
        tags=tags,
        timestamp=timestamp
    )
    db.session.add(new_entry)
    db.session.commit()

    return redirect(url_for('main.index'))

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_health_data(id):
    entry = HealthData.query.get_or_404(id)
    if request.method == 'POST':
        systolic = request.form.get('systolic')
        diastolic = request.form.get('diastolic')
        heart_rate = request.form.get('heart_rate')
        tags = request.form.get('tags')
        timestamp_str = request.form.get('timestamp')

        # Validate systolic pressure
        sys_valid, sys_result = validate_systolic(systolic)
        if not sys_valid:
            flash(sys_result)
            return redirect(url_for('main.edit_health_data', id=id))
        systolic_value = sys_result

        # Validate diastolic pressure
        dias_valid, dias_result = validate_diastolic(diastolic)
        if not dias_valid:
            flash(dias_result)
            return redirect(url_for('main.edit_health_data', id=id))
        diastolic_value = dias_result

        # Ensure systolic is greater than diastolic
        if systolic_value <= diastolic_value:
            flash("Systolic pressure must be greater than diastolic pressure")
            return redirect(url_for('main.edit_health_data', id=id))

        # Validate heart rate
        hr_valid, hr_result = validate_heart_rate(heart_rate)
        if not hr_valid:
            flash(hr_result)
            return redirect(url_for('main.edit_health_data', id=id))
        heart_rate_value = hr_result

        # Process timestamp
        if timestamp_str:
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Invalid date format")
                return redirect(url_for('main.edit_health_data', id=id))
        else:
            timestamp = datetime.utcnow()

        # Update the health data entry
        entry.systolic = systolic_value
        entry.diastolic = diastolic_value
        entry.heart_rate = heart_rate_value
        entry.tags = tags
        entry.timestamp = timestamp

        db.session.commit()
        return redirect(url_for('main.index'))

    return render_template('edit.html', entry=entry)

@bp.route('/delete/<int:id>', methods=['POST'])
def delete_health_data(id):
    entry = HealthData.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted successfully')
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
        allowed_extensions = {'csv', 'xlsx', 'xls', 'txt'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            flash(f'File type not allowed. Please upload a CSV, Excel, or TXT file.')
            return redirect(request.url)
            
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads')
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
            else:
                import_format = 'text'
        
        # Import based on format
        results = None
        try:
            if import_format == 'csv':
                results = DataImporter.import_from_csv(filepath, date_format=date_format)
            elif import_format == 'excel':
                results = DataImporter.import_from_excel(filepath)
            elif import_format == 'text':
                results = DataImporter.import_from_text(filepath, delimiter=delimiter, date_format=date_format)
            else:
                flash(f'Unsupported import format: {import_format}')
                return redirect(request.url)
                
            # Show import results
            flash(f'Import completed: {results["success"]} records imported successfully, {results["failure"]} failures')
            
            # Show errors if any
            if results['errors']:
                for error in results['errors'][:5]:  # Show only first 5 errors to avoid overwhelming the user
                    flash(f'Error: {error}')
                if len(results['errors']) > 5:
                    flash(f'...and {len(results["errors"]) - 5} more errors')
                    
            return redirect(url_for('main.index'))
            
        except Exception as e:
            flash(f'Import failed: {str(e)}')
            return redirect(request.url)
            
    # GET request - show import form
    return render_template('import.html')

@bp.route('/chart')
def chart():
    # Fetch all health data entries from the database, ordered by timestamp
    entries = HealthData.query.order_by(HealthData.timestamp).all()
    
    # Format timestamps as strings that JavaScript can understand
    formatted_timestamps = [entry.timestamp.strftime('%Y-%m-%d %H:%M:%S') for entry in entries]
    systolic_values = [entry.systolic for entry in entries]
    diastolic_values = [entry.diastolic for entry in entries]
    
    # Create data points for the chart
    data_points = []
    for i in range(len(entries)):
        data_points.append({
            'x': formatted_timestamps[i],
            'systolic': systolic_values[i],
            'diastolic': diastolic_values[i]
        })
    
    print(f"Formatted Timestamps: {formatted_timestamps}")  # Debug information
    print(f"Systolic Values: {systolic_values}")  # Debug information
    print(f"Diastolic Values: {diastolic_values}")  # Debug information
    
    return render_template('chart.html', 
                          timestamps=formatted_timestamps, 
                          systolic_values=systolic_values, 
                          diastolic_values=diastolic_values,
                          data_points=data_points)

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