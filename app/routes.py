from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import db, HealthData, Person
from datetime import datetime

# Create a Blueprint for the routes
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Fetch all health data entries from the database, ordered by timestamp
    entries = HealthData.query.order_by(HealthData.timestamp.desc()).all()
    persons = Person.query.all()
    return render_template('index.html', entries=entries, persons=persons)

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
    person_id = request.form.get('person_id')
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
        person_id=person_id,
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
        person_id = request.form.get('person_id')
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
        entry.person_id = person_id
        entry.systolic = systolic_value
        entry.diastolic = diastolic_value
        entry.heart_rate = heart_rate_value
        entry.tags = tags
        entry.timestamp = timestamp

        db.session.commit()
        return redirect(url_for('main.index'))

    persons = Person.query.all()
    return render_template('edit.html', entry=entry, persons=persons)

@bp.route('/delete/<int:id>', methods=['POST'])
def delete_health_data(id):
    entry = HealthData.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted successfully')
    return redirect(url_for('main.index'))

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

@bp.route('/register', methods=['GET', 'POST'])
def register_person():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        description = request.form.get('description')

        new_person = Person(
            name=name,
            age=age,
            gender=gender,
            description=description
        )
        db.session.add(new_person)
        db.session.commit()
        flash('Person registered successfully')
        return redirect(url_for('main.index'))

    return render_template('register.html')

@bp.route('/persons')
def list_persons():
    persons = Person.query.all()
    return render_template('persons.html', persons=persons)

@bp.route('/person/<int:id>')
def view_person(id):
    person = Person.query.get_or_404(id)
    return render_template('person.html', person=person)
