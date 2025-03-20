from datetime import datetime
from .models import db, HealthData

class HealthDataHandler:
    def validate_systolic(self, systolic_str):
        try:
            systolic = int(systolic_str)
            if not (100 <= systolic <= 200):
                return False, "Systolic pressure must be between 100-200"
            return True, systolic
        except:
            return False, "Systolic pressure must be a number"

    def validate_diastolic(self, diastolic_str):
        try:
            diastolic = int(diastolic_str)
            if not (60 <= diastolic <= 160):
                return False, "Diastolic pressure must be between 60-160"
            return True, diastolic
        except:
            return False, "Diastolic pressure must be a number"

    def validate_heart_rate(self, hr_str):
        try:
            hr = int(hr_str)
            if not (50 <= hr <= 200):
                return False, "Heart rate must be between 50-200"
            return True, hr
        except:
            return False, "Heart rate must be a number"

    def add_entry(self, form_data, user_id=None):
        try:
            # Validate data
            valid, systolic = self.validate_systolic(form_data['systolic'])
            if not valid:
                return {'success': False, 'message': systolic}

            valid, diastolic = self.validate_diastolic(form_data['diastolic'])
            if not valid:
                return {'success': False, 'message': diastolic}

            valid, heart_rate = self.validate_heart_rate(form_data['heart_rate'])
            if not valid:
                return {'success': False, 'message': heart_rate}

            timestamp = form_data['timestamp']
            tags = form_data['tags']

            existing_entry = HealthData.query.filter_by(timestamp=timestamp).first()
            if existing_entry:
                return {'success': False, 'message': 'A record with the same date and time already exists.'}

            new_entry = HealthData(timestamp=timestamp, systolic=systolic, diastolic=diastolic, heart_rate=heart_rate, tags=tags, user_id=user_id)
            db.session.add(new_entry)
            db.session.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def update_entry(self, entry_id, data, user_id=None):
        try:
            # Validate data
            valid, systolic = self.validate_systolic(data['systolic'])
            if not valid:
                return {'success': False, 'message': systolic}

            valid, diastolic = self.validate_diastolic(data['diastolic'])
            if not valid:
                return {'success': False, 'message': diastolic}

            valid, heart_rate = self.validate_heart_rate(data['heart_rate'])
            if not valid:
                return {'success': False, 'message': heart_rate}

            timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%dT%H:%M')
            tags = data['tags']

            entry = HealthData.query.get(entry_id)
            if not entry:
                return {'success': False, 'message': 'Entry not found.'}

            existing_entry = HealthData.query.filter_by(timestamp=timestamp).first()
            if existing_entry and existing_entry.id != entry_id:
                return {'success': False, 'message': 'A record with the same date and time already exists.'}

            entry.timestamp = timestamp
            entry.systolic = systolic
            entry.diastolic = diastolic
            entry.heart_rate = heart_rate
            entry.tags = tags
            db.session.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def import_data(self, data):
        try:
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
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def delete_entry(self, entry_id):
        try:
            entry = HealthData.query.get(entry_id)
            if not entry:
                return {'success': False, 'message': 'Entry not found.'}

            db.session.delete(entry)
            db.session.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}

# Generated by Copilot
