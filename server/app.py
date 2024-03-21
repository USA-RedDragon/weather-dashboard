import calendar
import os
import logging

from flask import Flask, send_file, jsonify
import metpy
from metpy.io import Level2File
from metpy.units import units
import msgpack
import numpy as np

from .radar import get_radar_scan_time, extract_timestamp, get_specific_radar_scan

app = Flask(__name__)

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
    obj = get_specific_radar_scan(station, timestamp)
    f = Level2File(obj['Body'])

    # First item in ray is header, which has azimuth angle
    az = np.array([ray[0].az_angle for ray in f.sweeps[sweep]])
    diff = np.diff(az)
    crossed = diff < -180
    diff[crossed] += 360.
    avg_spacing = diff.mean()

    # Convert mid-point to edge
    az = (az[:-1] + az[1:]) / 2
    az[crossed] += 180.

    # Concatenate with overall start and end of data we calculate using the average spacing
    az = np.concatenate(([az[0] - avg_spacing], az, [az[-1] + avg_spacing]))
    az = units.Quantity(az, 'degrees')

    ref_hdr = f.sweeps[sweep][0][4][b'REF'][0]
    ref_range = (np.arange(ref_hdr.num_gates + 1) - 0.5) * ref_hdr.gate_width + ref_hdr.first_gate
    ref_range = units.Quantity(ref_range, 'kilometers')
    ref = np.array([ray[4][b'REF'][1] for ray in f.sweeps[sweep]])

    # Extract central longitude and latitude from file
    cent_lon = f.sweeps[0][0][1].lon
    cent_lat = f.sweeps[0][0][1].lat

    data = np.ma.array(ref)
    data[np.isnan(data)] = np.ma.masked

    xlocs, ylocs = metpy.calc.azimuth_range_to_lat_lon(az, ref_range, cent_lon, cent_lat)

    packed = msgpack.packb(
        {
        'xlocs': xlocs.tolist(),
        'ylocs': ylocs.tolist(),
        'data': data.tolist(),
        'timestamp': timestamp,
        }
    )

    return packed, 200, {'Content-Type': 'application/msgpack'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host="0.0.0.0", port=5000)
