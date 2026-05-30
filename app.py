
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import math

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


#classes
class ParamsDB(db.Model):
    __tablename__ = "paramsDB"

    id = db.Column(db.Integer, primary_key=True)

    targetVPD = db.Column(db.Float, nullable=False)
    targetHumid = db.Column(db.Float, nullable=False)
    targetTemp = db.Column(db.Float, nullable=False)
    uploadInterval = db.Column(db.Integer, nullable=False)
    sensitivity = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    
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





#methods
def calculate_vpd(temp_c, rh):

    svp = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    avp = svp * (rh / 100.0)

    return round(svp - avp, 3)




@app.route("/")
def home():
    return "Weather API is running!"

# Create database tables
@app.route("/init-db")
def init_db():
    db.create_all()
    return "Database initialized!"

@app.route("/rebuild-db")
def rebuild_db():

    try:

        #ParamsDB.__table__.drop(db.engine)
        db.drop_all()
        db.create_all()

        return "Database rebuilt successfully!"

    except Exception as e:

        return str(e), 500


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
        uploadInterval = data.get("uploadInterval")
        sensitivity = data.get("sensitivity")
        


        if (targetVPD is None or targetHumid is None or targetTemp is None or uploadInterval is None):
            return jsonify({"error": "Missing required fields"}), 400

        # Use latest row only
        params = ParamsDB.query.first()

        if params:

            params.targetVPD = targetVPD
            params.targetHumid = targetHumid
            params.targetTemp = targetTemp
            params.uploadInterval = uploadInterval
            params.sensitivity = sensitivity

        else:

            params = ParamsDB(
                targetVPD=targetVPD,
                targetHumid=targetHumid,
                targetTemp=targetTemp,
                uploadInterval=uploadInterval,
                sensitivity=sensitivity
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
            "uploadInterval": params.uploadInterval,
            "sensitivity": params.sensitivity,
            "created_at": params.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500



@app.route("/graph")
def graph():

    TIMEZONES = [
        "America/Denver",
        "America/Chicago",
        "America/New_York",
        "America/Los_Angeles",
        "UTC"
    ]

    timezone_name = request.args.get("timezone","America/Denver")

    selected_location = int(
        request.args.get("location", 1)
    )

    available_locations = [row[0]
    for row in
        db.session.query(WeatherData.location)

    .distinct()

    .order_by(WeatherData.location)

    ]

    start_str = request.args.get("start")
    end_str = request.args.get("end")

    # Default = last 24 hours

    if not start_str or not end_str:

        end_time = datetime.utcnow()

        start_time = (
            end_time -
            timedelta(hours=24)
        )

    else:

        try:
            local_tz = ZoneInfo(timezone_name)
            
            start_time = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
            
            end_time = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
            
            # Attach selected timezone
            
            start_time = start_time.replace(tzinfo=local_tz)
            
            end_time = end_time.replace(tzinfo=local_tz)
            
            # Convert to UTC for querying database
            
            start_time = start_time.astimezone(
                ZoneInfo("UTC")
            ).replace(tzinfo=None)
            
            end_time = end_time.astimezone(
                ZoneInfo("UTC")
            ).replace(tzinfo=None)

        except Exception:

            return (
                "Invalid datetime format."
                " Use datetime-local inputs."
            ), 400

    entries = (
    
        WeatherData.query
    
        .filter(WeatherData.location == selected_location)
    
        .filter(WeatherData.created_at >= start_time, WeatherData.created_at <= end_time)
    
        .order_by(WeatherData.created_at.asc())
    
        .all()
    
    )

    timestamps = []
    temperatures = []
    humidities = []
    vpd_values = []

    for entry in entries:

        local_time = (
            entry.created_at
            .replace(tzinfo=ZoneInfo("UTC"))
            .astimezone(ZoneInfo(timezone_name))
        )

        timestamps.append(
            local_time.strftime("%Y-%m-%d %H:%M")
        )

        temperatures.append(
            entry.temperature
        )

        humidities.append(
            entry.humidity
        )

        vpd_values.append(
            calculate_vpd(entry.temperature,entry.humidity)
        )

    local_start = (
        start_time
        .replace(tzinfo=ZoneInfo("UTC"))
        .astimezone(local_tz)
    )
    
    local_end = (
        end_time
        .replace(tzinfo=ZoneInfo("UTC"))
        .astimezone(local_tz)
    )

    return render_template_string("""

<!DOCTYPE html>

<html>

<head>

<title>Weather Dashboard</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>

body {

    font-family: Arial;
    margin: 20px;

}

form {

    margin-bottom: 25px;

}

canvas {

    max-width: 1400px;
    margin-bottom: 50px;

}

</style>

</head>

<body>

<h1>Grow Dome Data
(Location {{ selected_location }})
</h1>

<form method="GET">

    <label>Start:</label>

    <input
        type="datetime-local"
        name="start"
        value="{{ start_date }}"
    >

    <label>End:</label>

    <input
        type="datetime-local"
        name="end"
        value="{{ end_date }}"
    >

    <label>Timezone:</label>

    <select name="timezone">

        {% for tz in timezones %}

        <option
            value="{{ tz }}"
            {% if tz == current_timezone %}
            selected
            {% endif %}
        >

            {{ tz }}

        </option>

        {% endfor %}

    </select>

    <label>Location:</label>

    <select name="location">
    
        {% for loc in available_locations %}
    
        <option
            value="{{ loc }}"
            {% if loc == selected_location %}
            selected
            {% endif %}
        >
    
            Location {{ loc }}
    
        </option>
    
        {% endfor %}
    
    </select>

    <button type="submit">

        Update Graph

    </button>

</form>

<h2>Temperature & Humidity</h2>

<canvas id="weatherChart"></canvas>

<h2>VPD</h2>

<canvas id="vpdChart"></canvas>

<script>

const labels =
    {{ timestamps | tojson }};

const temperatures =
    {{ temperatures | tojson }};

const humidities =
    {{ humidities | tojson }};

const vpdValues =
    {{ vpd_values | tojson }};

new Chart(

    document.getElementById(
        'weatherChart'
    ),

    {

        type: 'line',

        data: {

            labels: labels,

            datasets: [

                {

                    label:
                    'Temperature (°C)',

                    data:
                    temperatures,

                    yAxisID:
                    'tempAxis',

                    borderWidth: 2

                },

                {

                    label:
                    'Humidity (%)',

                    data:
                    humidities,

                    yAxisID:
                    'humidAxis',

                    borderWidth: 2

                }

            ]

        },

        options: {

            responsive: true,

            scales: {

                tempAxis: {

                    type: 'linear',

                    position: 'left'

                },

                humidAxis: {

                    type: 'linear',

                    position: 'right'

                }

            }

        }

    }

);

new Chart(

    document.getElementById(
        'vpdChart'
    ),

    {

        type: 'line',

        data: {

            labels: labels,

            datasets: [

                {

                    label:
                    'VPD (kPa)',

                    data:
                    vpdValues,

                    borderWidth: 2

                }

            ]

        },

        options: {

            responsive: true

        }

    }

);

</script>

</body>

</html>


""",

        timestamps=timestamps,

        temperatures=temperatures,

        humidities=humidities,

        vpd_values=vpd_values,
                                  
        start_date=local_start.strftime("%Y-%m-%dT%H:%M"),
        
        end_date=local_end.strftime("%Y-%m-%dT%H:%M"),

        timezones=TIMEZONES,

        available_locations=available_locations,

        selected_location=selected_location,

        current_timezone=timezone_name

    )





if __name__ == "__main__":
    #with app.app_context():
        #db.drop_all()
        #db.create_all()
        #ParamsDB.__table__.drop(db.engine)
        #ParamsDB.__table__.create(db.engine)

    
    app.run(host="0.0.0.0", port=8080)
