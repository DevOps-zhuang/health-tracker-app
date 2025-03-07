import logging
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from datetime import datetime
from .models import db, HealthData

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create a Blueprint for the routes
bp = Blueprint('api', __name__)

@bp.route('/add', methods=['POST'])
def add_entry():
    timestamp = request.form['timestamp']
    systolic = request.form['systolic']
    diastolic = request.form['diastolic']
    heart_rate = request.form['heart_rate']
    tags = request.form['tags']

    existing_entry = HealthData.query.filter_by(timestamp=timestamp).first()
    if existing_entry:
        flash('A record with the same date and time already exists.')
        return redirect(url_for('main.index'))

    new_entry = HealthData(timestamp=timestamp, systolic=systolic, diastolic=diastolic, heart_rate=heart_rate, tags=tags)
    db.session.add(new_entry)
    db.session.commit()
    flash('Entry added successfully!')
    return redirect(url_for('main.index'))

@bp.route('/update/<int:entry_id>', methods=['POST'])
def update_entry(entry_id):
    logging.debug(f'Updating entry with ID: {entry_id}')
    try:
        data = request.get_json()
        logging.debug(f'Received data: {data}')
        
        timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%dT%H:%M')
        systolic = int(data['systolic'])
        diastolic = int(data['diastolic'])
        heart_rate = int(data['heart_rate'])
        tags = data['tags']

        entry = HealthData.query.get(entry_id)
        if not entry:
            logging.debug('Entry not found')
            return jsonify({'success': False, 'message': 'Entry not found.'}), 404

        existing_entry = HealthData.query.filter_by(timestamp=timestamp).first()
        if existing_entry and existing_entry.id != entry_id:
            logging.debug('Duplicate entry found with the same timestamp')
            return jsonify({'success': False, 'message': 'A record with the same date and time already exists.'})

        entry.timestamp = timestamp
        entry.systolic = systolic
        entry.diastolic = diastolic
        entry.heart_rate = heart_rate
        entry.tags = tags
        db.session.commit()
        logging.debug('Entry updated successfully')
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f'Error updating entry: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/import', methods=['POST'])
def import_data():
    data = request.get_json()
    for entry_data in data:
        timestamp = entry_data['timestamp']
        systolic = entry_data['systolic']
        diastolic = entry_data['diastolic']
        heart_rate = entry_data['heart_rate']
        tags = entry_data['tags']

        existing_entry = HealthData.query.filter_by(timestamp=timestamp).first()
        if existing_entry:
            continue  # Skip duplicate entries

        new_entry = HealthData(timestamp=timestamp, systolic=systolic, diastolic=diastolic, heart_rate=heart_rate, tags=tags)
        db.session.add(new_entry)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    logging.debug(f'Deleting entry with ID: {entry_id}')
    try:
        entry = HealthData.query.get(entry_id)
        if not entry:
            logging.debug('Entry not found')
            return jsonify({'success': False, 'message': 'Entry not found.'}), 404

        db.session.delete(entry)
        db.session.commit()
        logging.debug('Entry deleted successfully')
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f'Error deleting entry: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500