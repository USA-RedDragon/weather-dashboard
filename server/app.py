import calendar
import datetime
import json
import logging
import os
import queue
import time

from flask import Flask, send_file, jsonify
from flask_sock import Sock
from simple_websocket import ConnectionClosed
from metpy.io import Level2File


from .radar import get_radar_scan_time, extract_timestamp, get_specific_radar_scan, process
from .cache import Cache
from .radar_watcher import RadarWatcher

dataTypes = ["coastline", "states", "lakes", "rivers", "freeways", "oklahomaCounties", "oklahomaLakes", "oklahomaStreams"]

app = Flask(__name__)
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
websocket = Sock(app)
cache = Cache()
watcher = RadarWatcher(cache)

watcher.start("KTLX")

# @app.errorhandler(Exception)
# def exception_handler(error):
#     return "!!!!"  + repr(error)

@websocket.route('/ws/watch/station/<station>')
def watch_station(ws, station):
    q = queue.Queue()
    eventListener = lambda station, ts: q.put(json.dumps({"station": station, "timestamp": ts}))
    watcher.add_event_listener(eventListener, station)
    if not watcher.is_watching(station):
        watcher.start(station)
    ws.send('PONG')
    while True:
        try:
            data = ws.receive(timeout=2)
            if data == 'close':
                break
            elif data == 'PING':
                ws.send('PONG')
            try:
                data = q.get_nowait()
            except queue.Empty:
                continue
            else:
                ws.send(data)
        except ConnectionClosed:
            break
    watcher.remove_event_listener(eventListener, station)

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
