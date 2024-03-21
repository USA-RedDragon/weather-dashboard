import datetime
import re

import boto3
import botocore
from botocore.client import Config

def get_radar_scan_time(station, last: int):
    # last is the offset from the most recent scan

    station = station.upper()
    s3 = boto3.resource('s3', config=Config(signature_version=botocore.UNSIGNED, user_agent_extra='Resource'))
    bucket = s3.Bucket('noaa-nexrad-level2')
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
    s3 = boto3.client('s3', config=Config(signature_version=botocore.UNSIGNED, user_agent_extra='Client'))
    # key is yyyy/mm/dd/{station}/{station}YYYYMMDD_HHMMSS_V06
    time = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    key = f"{time.strftime('%Y/%m/%d')}/{station}/{station}{time.strftime('%Y%m%d_%H%M%S')}_V06"
    try:
        obj = s3.get_object(Bucket='noaa-nexrad-level2', Key=key)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise ValueError("Radar scan not found")
        else:
            raise
    return obj
