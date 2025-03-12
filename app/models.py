from datetime import datetime
from app import db

class Person(db.Model):
    __tablename__ = 'person'
    
    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each person
    name = db.Column(db.String(100), nullable=False)  # Name of the person
    age = db.Column(db.Integer, nullable=False)  # Age of the person
    gender = db.Column(db.String(10), nullable=False)  # Gender of the person
    description = db.Column(db.String(255), nullable=True)  # Description of the person

    def __repr__(self):
        return f'<Person {self.id}: Name={self.name}, Age={self.age}, Gender={self.gender}, Description={self.description}>'

class HealthData(db.Model):
    __tablename__ = 'health_data'
    
    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each entry
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)  # Foreign key reference to the person
    systolic = db.Column(db.Integer, nullable=False)  # Systolic blood pressure (high value)
    diastolic = db.Column(db.Integer, nullable=False)  # Diastolic blood pressure (low value)
    heart_rate = db.Column(db.Integer, nullable=False)  # Heart rate reading
    tags = db.Column(db.String(100), nullable=True)  # Tags for categorizing the entry
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Timestamp for the entry
    
    person = db.relationship('Person', backref=db.backref('health_data', lazy=True))

    @property
    def blood_pressure(self):
        # Provide backward compatibility for templates still using blood_pressure
        return f"{self.systolic}/{self.diastolic}"
    
    def __repr__(self):
        return f'<HealthData {self.id}: PersonID={self.person_id}, BP={self.systolic}/{self.diastolic}, HR={self.heart_rate}, Time={self.timestamp}>'
