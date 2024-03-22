import calendar
import datetime
import os
import logging
import time

from flask import Flask, send_file, jsonify
import metpy
from metpy.io import Level2File


from .radar import get_radar_scan_time, extract_timestamp, get_specific_radar_scan, process
from .cache import Cache

app = Flask(__name__)
cache = Cache()

dataTypes = ["coastline", "states", "lakes", "rivers", "freeways", "oklahomaCounties", "oklahomaLakes", "oklahomaStreams"]

# @app.errorhandler(Exception)
# def exception_handler(error):
#     return "!!!!"  + repr(error)

@app.route("/api/geojson/<data>/<version>", methods=["GET"])
def get_geojson(data, version):
    if data not in dataTypes:
        return "Invalid data type", 404
    
    local = os.path.dirname(os.path.realpath(__file__))

    if not os.path.exists(f"{local}/geojson/v{version}"):
        return "Invalid version", 404

    if not os.path.exists(f"{local}/geojson/v{version}/{data}.json"):
        print(f"File not found: ./geojson/v{version}/{data}.json")
        return "Internal server error", 500

    return send_file(f"{local}/geojson/v{version}/{data}.json", mimetype="application/json")

@app.route("/api/radar/<station>/scan/<int:last>", methods=["GET"])
def get_radar_station_last_scan(station, last):
    obj = get_radar_scan_time(station, last)
    timestamp = extract_timestamp(obj, station)
    return jsonify({"timestamp": calendar.timegm(timestamp.utctimetuple())})

@app.route("/api/radar/<station>/<int:sweep>/<int:timestamp>", methods=["GET"])
def get_radar(station, sweep, timestamp):
    timeStart = time.monotonic()
    if cache.has(f"{station}/{sweep}/{timestamp}"):
        logging.info("Cache hit")
        packed = cache.get(f"{station}/{sweep}/{timestamp}")
        downloadCompleteTime = time.monotonic()
    else:
        obj = get_specific_radar_scan(station, timestamp)
        f = Level2File(obj['Body'])
        downloadCompleteTime = time.monotonic()
        packed = process(f, sweep, timestamp)
        cache.set(f"{station}/{sweep}/{timestamp}", packed)
    timeEnd = time.monotonic()
    logging.info(f"get_radar took {datetime.timedelta(seconds=timeEnd - timeStart)}")
    logging.info(f"get_radar download took {datetime.timedelta(seconds=downloadCompleteTime - timeStart)}")

    return packed, 200, {'Content-Type': 'application/msgpack'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host="0.0.0.0", port=5000)
