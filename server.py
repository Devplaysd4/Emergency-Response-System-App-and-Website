from flask import Flask, request, jsonify, send_from_directory
import logging
import json
import hashlib
import os
from datetime import datetime
from werkzeug.utils import secure_filename

logging.basicConfig(filename='server.log', level=logging.DEBUG)

app = Flask(__name__)

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())


def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

@app.route("/")
def index():
    return send_from_directory('.', 'MAIN.html')

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory('.', path)

@app.route("/sos", methods=["POST"])
def sos():
    app.logger.info("SOS ENDPOINT CALLED")
    app.logger.info("Received request at /sos")
    try:
        data = request.get_json()
        data['timestamp'] = datetime.now().isoformat()
        app.logger.info("Received SOS data: %s", data)
        try:
            with open("alert.json", "r") as f:
                alerts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            alerts = []
        alerts.append(data)
        with open("alert.json", "w") as f:
            json.dump(alerts, f)
        return jsonify({"status": "success"})
    except Exception as e:
        app.logger.error("Error processing SOS request: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/sos_alerts")
def get_sos_alerts():
    try:
        with open("alert.json", "r") as f:
            alerts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        alerts = []
    return jsonify(alerts)

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    mobile = data.get("mobile")
    kyc = data.get("kyc")
    emergency_contact = data.get("emergency_contact")

    if not all([mobile, kyc, emergency_contact]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    users = load_users()

    if any(user['mobile'] == mobile for user in users):
        return jsonify({"status": "error", "message": "User already exists"}), 400

    blockchain_id = hashlib.sha256(mobile.encode('utf-8')).hexdigest()
    new_user = {
        "mobile": mobile,
        "kyc": kyc,
        "emergency_contact": emergency_contact,
        "blockchain_id": blockchain_id
    }
    users.append(new_user)
    save_users(users)

    return jsonify({"status": "success", "user": new_user}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    mobile = data.get("mobile")

    if not mobile:
        return jsonify({"status": "error", "message": "Mobile number is required"}), 400

    users = load_users()
    user_found = next((user for user in users if user['mobile'] == mobile), None)

    if user_found:
        return jsonify({"status": "success", "user": user_found})
    else:
        return jsonify({"status": "error", "message": "User not found"}), 404


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/report", methods=["POST"])
def report():
    app.logger.info("REPORT ENDPOINT CALLED")
    try:
        if 'image' not in request.files:
            return jsonify({"status": "error", "message": "No image part"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            filepath = os.path.join('website', 'uploads', unique_filename)
            file.save(filepath)

            reason = request.form.get('reason', '')
            user_json = request.form.get('user', '{}')
            location_json = request.form.get('location', '{}')
            
            user_data = json.loads(user_json)
            location_data = json.loads(location_json)

            try:
                with open("website/reports.json", "r") as f:
                    reports = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                reports = []
            
            new_report = {
                "id": unique_filename,
                "timestamp": datetime.now().isoformat(),
                "image_path": f"uploads/{unique_filename}",
                "reason": reason,
                "user": user_data,
                "location": location_data,
                "status": "pending"
            }
            
            reports.append(new_report)
            
            with open("website/reports.json", "w") as f:
                json.dump(reports, f, indent=4)
                
            return jsonify({"status": "success", "message": "Report submitted."})
        else:
            return jsonify({"status": "error", "message": "File type not allowed"}), 400

    except Exception as e:
        app.logger.error("Error processing report request: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get_reports")
def get_reports():
    app.logger.info("GET REPORTS ENDPOINT CALLED")
    try:
        with open("website/reports.json", "r") as f:
            reports = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        reports = []
    return jsonify(reports)

@app.route("/accept_report", methods=["POST"])
def accept_report():
    app.logger.info("ACCEPT REPORT ENDPOINT CALLED")
    try:
        data = request.get_json()
        report_id = data.get('id')
        if not report_id:
            return jsonify({"status": "error", "message": "Report ID is required"}), 400

        with open("website/reports.json", "r") as f:
            reports = json.load(f)
        
        report_found = False
        for report in reports:
            if report.get('id') == report_id:
                report['status'] = 'accepted'
                report_found = True
                break
        
        if not report_found:
            return jsonify({"status": "error", "message": "Report not found"}), 404
            
        with open("website/reports.json", "w") as f:
            json.dump(reports, f, indent=4)
            
        return jsonify({"status": "success", "message": "Report accepted."})

    except Exception as e:
        app.logger.error("Error processing accept_report request: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/delete_report", methods=["POST"])
def delete_report():
    app.logger.info("DELETE REPORT ENDPOINT CALLED")
    try:
        data = request.get_json()
        report_id = data.get('id')
        if not report_id:
            return jsonify({"status": "error", "message": "Report ID is required"}), 400

        with open("website/reports.json", "r") as f:
            reports = json.load(f)
        
        report_to_delete = next((r for r in reports if r.get('id') == report_id), None)
        if not report_to_delete:
            return jsonify({"status": "error", "message": "Report not found"}), 404
            
        reports = [r for r in reports if r.get('id') != report_id]
        
        with open("website/reports.json", "w") as f:
            json.dump(reports, f, indent=4)
            
        image_path = os.path.join('website', report_to_delete['image_path'])
        if os.path.exists(image_path):
            os.remove(image_path)
            
        return jsonify({"status": "success", "message": "Report deleted."})

    except Exception as e:
        app.logger.error("Error processing delete_report request: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
