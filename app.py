
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

#config
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class WeatherData(db.Model):
    __tablename__ = "weather_data"

    id = db.Column(db.Integer, primary_key=True)

    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    location = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    
class ParamsDB(db.Model):
    __tablename__ = "paramsDB"

    id = db.Column(db.Integer, primary_key=True)

    targetVPD = db.Column(db.Float, nullable=False)
    targetHumid = db.Column(db.Float, nullable=False)
    targetTemp = db.Column(db.Float, nullable=False)
    getPostInt = db.Column(db.Float, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )



@app.route("/")
def home():
    return "Weather API is running!"

# Create database tables
@app.route("/init-db")
def init_db():
    db.create_all()
    return "Database initialized!"

# Receive sensor data
@app.route("/data", methods=["POST"])
def receive_data():

    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    temperature = data.get("temperature")
    humidity = data.get("humidity")
    location = data.get("location")

    if temperature is None or humidity is None or location is None:
        return jsonify({"error": "Missing required fields"}), 400

    try:

        new_entry = WeatherData(
            temperature=temperature,
            humidity=humidity,
            location=location
        )

        db.session.add(new_entry)
        db.session.commit()

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# # Get all data
# @app.route("/data", methods=["GET"])
# def get_data():

#     entries = WeatherData.query.all()

#     output = []

#     for entry in entries:
#         output.append({
#             "id": entry.id,
#             "temperature": entry.temperature,
#             "humidity": entry.humidity,
#             "location": entry.location,
#             "created_at": entry.created_at
#         })

#     return jsonify(output)

@app.route("/data", methods=["GET"])
def get_data():

    try:

        query = WeatherData.query

        #id
        start_id = request.args.get("start_id")
        end_id = request.args.get("end_id")

        if start_id:
            query = query.filter(WeatherData.id >= int(start_id))

        if end_id:
            query = query.filter(WeatherData.id <= int(end_id))

        
        #date
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Format:
        # 2026-05-18 12:00:00

        if start_date:
            start_date_obj = datetime.strptime(
                start_date,
                "%Y-%m-%d %H:%M:%S"
            )

            query = query.filter(
                WeatherData.created_at >= start_date_obj
            )

        if end_date:
            end_date_obj = datetime.strptime(
                end_date,
                "%Y-%m-%d %H:%M:%S"
            )

            query = query.filter(
                WeatherData.created_at <= end_date_obj
            )
            

        entries = query.all()

        output = []

        for entry in entries:

            output.append({
                "id": entry.id,
                "temperature": entry.temperature,
                "humidity": entry.humidity,
                "location": entry.location,
                "created_at": entry.created_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            })

        return jsonify(output)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/params", methods=["POST"])
def set_params():

    try:

        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        targetVPD = data.get("targetVPD")
        targetHumid = data.get("targetHumid")
        targetTemp = data.get("targetTemp")
        getPostInt = data.get("getPostInt")
        


        if (targetVPD is None or targetHumid is None or targetTemp is None or getPostInt is None):
            return jsonify({"error": "Missing required fields"}), 400

        # Use latest row only
        params = ParamsDB.query.first()

        if params:

            params.targetVPD = targetVPD
            params.targetHumid = targetHumid
            params.targetTemp = targetTemp
            params.getPostInt = getPostInt

        else:

            params = ParamsDB(
                targetVPD=targetVPD,
                targetHumid=targetHumid,
                targetTemp=targetTemp,
                getPostInt=getPostInt
            )

            db.session.add(params)

        db.session.commit()

        return jsonify({"status": "success"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

@app.route("/params", methods=["GET"])
def get_params():

    try:

        params = ParamsDB.query.first()

        if not params:

            return jsonify({
                "error": "No parameters found"
            }), 404

        return jsonify({

            "targetVPD": params.targetVPD,
            "targetHumid": params.targetHumid,
            "targetTemp": params.targetTemp,
            "getPostInt": params.getPostInt,
            "created_at": params.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
