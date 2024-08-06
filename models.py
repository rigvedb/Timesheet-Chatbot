# /timesheet_chatbot/models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TimesheetEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.String, nullable=False)

