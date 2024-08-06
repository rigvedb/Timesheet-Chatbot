from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models import db, TimesheetEntry
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import requests
import jwt  # Import jwt for token decoding

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timesheets.db'
app.config['JWT_SECRET_KEY'] = 'e5969c1b4aecf7d16862a9b99407d8b23e11cb1bbd7d8296'  # Replace with your generated key
db.init_app(app)
jwt = JWTManager(app)
CORS(app)  # Enable CORS for the app

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chatbot')
def chatbot():
    return app.send_static_file('chatbot.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Mock user data for demonstration; replace with actual user verification
    if username == 'rigvedbhargav' and password == 'password':
        token = create_access_token(identity=username)
        return jsonify(access_token=token), 200
    else:
        return jsonify({"msg": "Login failed"}), 401

@app.route('/timesheet', methods=['POST'])
@jwt_required()
def add_timesheet():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Create a new TimesheetEntry
    new_entry = TimesheetEntry(
        user_id=user_id,
        date=datetime.strptime(data['date'], '%Y-%m-%d'),
        hours=data['hours'],
        description=data['description']
    )
    db.session.add(new_entry)
    db.session.commit()
    
    return jsonify({"msg": "Timesheet entry added"}), 201

@app.route('/timesheet/<int:id>', methods=['PUT'])
@jwt_required()
def update_timesheet(id):
    user_id = get_jwt_identity()
    entry = TimesheetEntry.query.get(id)
    if entry and entry.user_id == user_id:
        data = request.get_json()
        if 'date' in data:
            entry.date = datetime.strptime(data['date'], '%Y-%m-%d')
        if 'hours' in data:
            entry.hours = data['hours']
        if 'description' in data:
            entry.description = data['description']
        db.session.commit()
        return jsonify({"msg": "Timesheet entry updated"}), 200
    return jsonify({"msg": "Entry not found or unauthorized"}), 404

@app.route('/timesheet/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_timesheet(id):
    user_id = get_jwt_identity()
    entry = TimesheetEntry.query.get(id)
    if entry and entry.user_id == user_id:
        db.session.delete(entry)
        db.session.commit()
        return jsonify({"msg": "Timesheet entry deleted"}), 200
    return jsonify({"msg": "Entry not found or unauthorized"}), 404

@app.route('/timesheet', methods=['GET'])
@jwt_required()
def view_timesheets():
    user_id = get_jwt_identity()
    entries = TimesheetEntry.query.filter_by(user_id=user_id).all()
    timesheets = [{
        "id": entry.id,
        "date": entry.date.strftime('%Y-%m-%d'),
        "hours": entry.hours,
        "description": entry.description
    } for entry in entries]
    return jsonify(timesheets), 200

@app.route('/chatbot/message', methods=['POST'])
def chatbot_message():
    message = request.get_json().get('message')
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"response": "Authorization token missing"}), 401

    try:
        token = auth_header.split(' ')[1]
        jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
    except IndexError:
        return jsonify({"response": "Invalid authorization header format"}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({"response": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"response": "Invalid token"}), 401

    try:
        response = handle_chatbot_message(message, token)
        return jsonify({"response": response})
    except Exception as e:
        app.logger.error(f"Error handling chatbot message: {e}")
        return jsonify({"response": "An error occurred while processing your request."}), 500

def handle_chatbot_message(message, token):
    message = message.lower().strip()

    if 'add timesheet' in message:
        return "Please provide the details in this format: Date (YYYY-MM-DD), Hours, Description."

    elif 'date:' in message and 'hours:' in message and 'description:' in message:
        try:
            lines = message.split(',')
            date_line = next(line for line in lines if 'date:' in line).split(':', 1)[1].strip()
            hours_line = next(line for line in lines if 'hours:' in line).split(':', 1)[1].strip()
            description_line = next(line for line in lines if 'description:' in line).split(':', 1)[1].strip()
            result = process_add_timesheet(date_line, hours_line, description_line, token)
            return result

        except Exception as e:
            return "There was an error processing your request. Please ensure the format is correct."

    elif 'view timesheets' in message:
        return "Fetching your timesheets..."
    elif 'delete timesheet' in message:
        return "Please provide the ID of the timesheet you want to delete."
    else:
        return "I didn't understand that. You can ask me to add, view, or delete timesheets."

def process_add_timesheet(date, hours, description, token):
    try:
        response = requests.post(
            'http://127.0.0.1:5000/timesheet',
            json={'date': date, 'hours': hours, 'description': description},
            headers={'Authorization': f'Bearer {token}'}
        )
        if response.status_code == 201:
            return "Timesheet entry added successfully!"
        else:
            return f"Failed to add timesheet entry. Status code: {response.status_code}"
    except Exception as e:
        return f"Error connecting to the server: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
