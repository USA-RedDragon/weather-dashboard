import datetime
import re

import boto3
import botocore
from botocore.client import Config
from metpy.units import units
import msgpack
import numpy as np

s3Resource = boto3.resource('s3', config=Config(signature_version=botocore.UNSIGNED, user_agent_extra='Resource'))
s3Client = boto3.client('s3', config=Config(signature_version=botocore.UNSIGNED, user_agent_extra='Client'))
bucket = s3Resource.Bucket('noaa-nexrad-level2')

def get_radar_scan_time(station, last: int):
    # last is the offset from the most recent scan
    station = station.upper()
    # Search for the latest file matching the format "yyyy/mm/dd/{station}/{station}{time}_V06"
    utcdate = datetime.datetime.now(datetime.UTC)
    prefix = f"{utcdate.strftime('%Y/%m/%d')}/{station}/{station}{utcdate.strftime('%Y%m%d_%H')}"
    # Strip out any objects whose key ends in _MDM
    objs = [obj for obj in list(bucket.objects.filter(Prefix=prefix)) if not obj.key.endswith('_MDM')]
    if len(objs) == 0:
        # This could be a new hour, so try the previous hour
        utcdate -= datetime.timedelta(hours=1)
        prefix = f"{utcdate.strftime('%Y/%m/%d')}/{station}/{station}{utcdate.strftime('%Y%m%d_%H')}"
        objs = [obj for obj in list(bucket.objects.filter(Prefix=prefix)) if not obj.key.endswith('_MDM')]
        if len(objs) == 0:
            # Is this a new day?
            utcdate += datetime.timedelta(hours=1)
            utcdate -= datetime.timedelta(days=1)
            prefix = f"{utcdate.strftime('%Y/%m/%d')}/{station}/{station}{utcdate.strftime('%Y%m%d_%H')}"
            objs = [obj for obj in list(bucket.objects.filter(Prefix=prefix)) if not obj.key.endswith('_MDM')]
            if len(objs) == 0:
                raise ValueError("No radar scans found")
    objs.sort(key=lambda x: x.key)
    if last >= len(objs):
        raise ValueError("Invalid last value")
    return objs[-(last+1)]

def extract_timestamp(obj, station):
    station = station.upper()
    # Strip out the "yyyy/mm/dd/{station}/{station}" prefix and _V06 suffix to get the timestamp
    regex = re.compile(r'\d{4}/\d{2}/\d{2}/' + station + '/' + station + r'(\d{8}_\d{6})_V06')
    match = regex.match(obj.key)
    if match is None:
        raise ValueError("Error parsing timestamp from key")
    return datetime.datetime.strptime(match.group(1), '%Y%m%d_%H%M%S')

def get_specific_radar_scan(station: str, timestamp: int):
    station = station.upper()
    # key is yyyy/mm/dd/{station}/{station}YYYYMMDD_HHMMSS_V06
    time = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    key = f"{time.strftime('%Y/%m/%d')}/{station}/{station}{time.strftime('%Y%m%d_%H%M%S')}_V06"
    try:
        obj = s3Client.get_object(Bucket='noaa-nexrad-level2', Key=key)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise ValueError("Radar scan not found")
        else:
            raise
    return obj

def process(f, sweep, timestamp):
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

    return msgpack.packb(
        {
        'cent_lon': cent_lon,
        'cent_lat': cent_lat,
        'az': az.m_as('degrees').tolist(),
        'ref_range': ref_range.m_as('meters').tolist(),
        'data': ref.tolist(),
        'timestamp': timestamp,
        }
    ) 