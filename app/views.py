import logging
from flask import Blueprint, request, jsonify, flash, redirect, url_for
from .utils import HealthDataHandler
from datetime import datetime
from .models import db, HealthData

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create a Blueprint for the routes
bp = Blueprint('api', __name__)

@bp.route('/add', methods=['POST'])
def add_entry():
    handler = HealthDataHandler()
    result = handler.add_entry(request.form)
    if result['success']:
        flash('Entry added successfully!')
    else:
        flash(result['message'])
    return redirect(url_for('main.index'))

@bp.route('/update/<int:entry_id>', methods=['POST'])
def update_entry(entry_id):
    logging.debug(f'Updating entry with ID: {entry_id}')
    try:
        data = request.get_json()
        logging.debug(f'Received data: {data}')
        
        handler = HealthDataHandler()
        result = handler.update_entry(entry_id, data)
        if result['success']:
            logging.debug('Entry updated successfully')
            return jsonify({'success': True})
        else:
            logging.debug(result['message'])
            return jsonify({'success': False, 'message': result['message']}), 404
    except Exception as e:
        logging.error(f'Error updating entry: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/import', methods=['POST'])
def import_data():
    data = request.get_json()
    handler = HealthDataHandler()
    result = handler.import_data(data)
    return jsonify(result)

@bp.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    logging.debug(f'Deleting entry with ID: {entry_id}')
    try:
        handler = HealthDataHandler()
        result = handler.delete_entry(entry_id)
        if result['success']:
            logging.debug('Entry deleted successfully')
            return jsonify({'success': True})
        else:
            logging.debug(result['message'])
            return jsonify({'success': False, 'message': result['message']}), 404
    except Exception as e:
        logging.error(f'Error deleting entry: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500