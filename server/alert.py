import datetime
import json

import requests
from shapely.geometry import shape, Polygon, MultiPolygon, GeometryCollection
from shapely import to_geojson
from awips.dataaccess import DataAccessLayer

from .cache import Cache

DataAccessLayer.changeEDEXHost("edex-cloud.unidata.ucar.edu")

class WXAlert(dict):
    # Event codes: https://www.weather.gov/nwr/eventcodes
    # https://www.weather.gov/help-map
    def _get_color(self):
        if self.get('event') == "Blizzard Warning":
            return "#FF4500"
        elif self.get('event') == "Coastal Flood Watch":
            return "#66CDAA"
        elif self.get('event') == "Coastal Flood Warning":
            return "#228B22"
        elif self.get('event') == "Dust Storm Warning":
            return "#FFE4C4"
        elif self.get('event') == "Extreme Wind Warning":
            return "#FF8C00"
        elif self.get('event') == "Flash Flood Watch":
            return "#2E8B57"
        elif self.get('event') == "Flash Flood Warning":
            return "#8B0000"
        elif self.get('event') == "Flash Flood Statement":
            return "#8B0000"
        elif self.get('event') == "Flood Watch":
            return "#2E8B57"
        elif self.get('event') == "Flood Warning":
            return "#00FF00"
        elif self.get('event') == "Flood Statement":
            return "#00FF00"
        elif self.get('event') == "High Wind Watch":
            return "#B8860B"
        elif self.get('event') == "High Wind Warning":
            return "#DAA520"
        elif self.get('event') == "Hurricane Watch":
            return "#FF00FF"
        elif self.get('event') == "Hurricane Warning":
            return "#DC143Cs"
        elif self.get('event') == "Hurricane Statement":
            return "#FFE4B5"
        elif self.get('event') == "Severe Thunderstorm Watch":
            return "#DB7093"
        elif self.get('event') == "Severe Thunderstorm Warning":
            return "#FFA500"
        elif self.get('event') == "Severe Weather Statement":
            return "#00FFFF"
        elif self.get('event') == "Snow Squall Warning":
            return "#C71585"
        elif self.get('event') == "Special Marine Warning":
            return "#FFA500"
        elif self.get('event') == "Special Weather Statement":
            return "#FFE4B5"
        elif self.get('event') == "Storm Surge Watch":
            return "#DB7FF7"
        elif self.get('event') == "Storm Surge Warning":
            return "#B524F7"
        elif self.get('event') == "Tornado Watch":
            return "#FFFF00"
        elif self.get('event') == "Tornado Warning":
            return "#FF0000"
        elif self.get('event') == "Tropical Storm Watch":
            return "#F08080"
        elif self.get('event') == "Tropical Storm Warning":
            return "#B22222"
        elif self.get('event') == "Tsunami Watch":
            return "#FF00FF"
        elif self.get('event') == "Tsunami Warning":
            return "#FD6347"
        elif self.get('event') == "Winter Storm Watch":
            return "#4682B4"
        elif self.get('event') == "Winter Storm Warning":
            return "#FF69B4"
        elif self.get('event') == "Avalanche Watch":
            return "#F4A460"
        elif self.get('event') == "Avalanche Warning":
            return "#1E90FF"
        elif self.get('event') == "Blue Alert":
            return "#B0C4DE"
        elif self.get('event') == "Child Abduction Emergency":
            return "#800000"
        elif self.get('event') == "Civil Danger Warning":
            return "#FFB6C1"
        elif self.get('event') == "Civil Emergency Message":
            return "#FFB6C1"
        elif self.get('event') == "Earthquake Warning":
            return "#8B4513"
        elif self.get('event') == "Evacuation Immediate":
            return "#7FFF00"
        elif self.get('event') == "Fire Warning":
            return "#A0522D"
        elif self.get('event') == "Hazardous Materials Warning":
            return "#4B0082"
        elif self.get('event') == "Law Enforcement Warning":
            return "#C0C0C0"
        elif self.get('event') == "Local Area Emergency":
            return "#C0C0C0"
        elif self.get('event') == "911 Telephone Outage Emergency":
            return "#C0C0C0"
        elif self.get('event') == "Nuclear Power Plant Warning":
            return "#4B0082"
        elif self.get('event') == "Radiological Hazard Warning":
            return "#4B0082"
        elif self.get('event') == "Shelter in Place Warning":
            return "#FA8072"
        elif self.get('event') == "Volcano Warning":
            return "#2F4F4F"
        else:
            return "#FD6347"
        
    def is_weather(self):
        if self.get('event') == "Blizzard Warning":
            return True
        elif self.get('event') == "Coastal Flood Watch":
            return True
        elif self.get('event') == "Coastal Flood Warning":
            return True
        elif self.get('event') == "Dust Storm Warning":
            return True
        elif self.get('event') == "Extreme Wind Warning":
            return True
        elif self.get('event') == "Flash Flood Watch":
            return True
        elif self.get('event') == "Flash Flood Warning":
            return True
        elif self.get('event') == "Flash Flood Statement":
            return True
        elif self.get('event') == "Flood Advisory":
            return True
        elif self.get('event') == "Flood Watch":
            return True
        elif self.get('event') == "Flood Warning":
            return True
        elif self.get('event') == "Flood Statement":
            return True
        elif self.get('event') == "High Wind Watch":
            return True
        elif self.get('event') == "High Wind Warning":
            return True
        elif self.get('event') == "Hurricane Watch":
            return True
        elif self.get('event') == "Hurricane Warning":
            return True
        elif self.get('event') == "Hurricane Statement":
            return True
        elif self.get('event') == "Severe Thunderstorm Watch":
            return True
        elif self.get('event') == "Severe Thunderstorm Warning":
            return True
        elif self.get('event') == "Severe Weather Statement":
            return True
        elif self.get('event') == "Snow Squall Warning":
            return True
        elif self.get('event') == "Special Marine Warning":
            return True
        elif self.get('event') == "Special Weather Statement":
            return True
        elif self.get('event') == "Storm Surge Watch":
            return True
        elif self.get('event') == "Storm Surge Warning":
            return True
        elif self.get('event') == "Tornado Watch":
            return True
        elif self.get('event') == "Tornado Warning":
            return True
        elif self.get('event') == "Tropical Storm Watch":
            return True
        elif self.get('event') == "Tropical Storm Warning":
            return True
        elif self.get('event') == "Tsunami Watch":
            return True
        elif self.get('event') == "Tsunami Warning":
            return True
        elif self.get('event') == "Winter Storm Watch":
            return True
        elif self.get('event') == "Winter Storm Warning":
            return True
        else:
            return False

    def __init__(self, feature_json, state, cache: Cache):
        if 'type' not in feature_json or feature_json['type'] != 'Feature':
            raise ValueError('Invalid GeoJSON Feature')
        if 'geometry' in feature_json and feature_json['geometry'] is not None:
            polygon = feature_json['geometry']
        else:
            polygon = self._make_multipolygon(cache, feature_json['properties']['affectedZones'])
        dict.__init__(self,
                    id=feature_json['properties']['id'],
                    geometry=polygon,
                    sent=feature_json['properties']['sent'],
                    expires=feature_json['properties']['expires'],
                    effective=feature_json['properties']['effective'],
                    onset=feature_json['properties']['onset'],
                    ends=feature_json['properties']['ends'],
                    message_type=feature_json['properties']['messageType'],
                    severity=feature_json['properties']['severity'],
                    certainty=feature_json['properties']['certainty'],
                    urgency=feature_json['properties']['urgency'],
                    event=feature_json['properties']['event'],
                    headline=feature_json['properties']['headline'],
                    description=feature_json['properties']['description'],
                    instruction=feature_json['properties']['instruction'] if 'instruction' in feature_json['properties'] else "",
                    area_desc=feature_json['properties']['areaDesc'],
                    state=state,
                    max_hail_size=feature_json['properties']['parameters']['maxHailSize'] if 'maxHailSize' in feature_json['properties']['parameters'] else None,
                    max_wind_speed=feature_json['properties']['parameters']['maxWindSpeed'] if 'maxWindSpeed' in feature_json['properties']['parameters'] else None,
                    color=self._get_color(),
                    is_weather=self.is_weather(),
                    )

    def _make_multipolygon(self, cache: Cache, affected_zones):
        ugcs_polygons = []
        for zone in affected_zones:
            poly = self._get_polygon_from_url(cache, zone)
            if type(poly) == Polygon:
                ugcs_polygons.append(poly)
            elif type(poly) == MultiPolygon:
                for geom in poly.geoms:
                    ugcs_polygons.append(geom)
            elif type(poly) == GeometryCollection:
                for geom in poly.geoms:
                    if type(geom) == Polygon:
                        ugcs_polygons.append(geom)
                    elif type(geom) == MultiPolygon:
                        for geom2 in geom.geoms:
                            ugcs_polygons.append(geom2)
                    else:
                        print(geom)
                        raise ValueError('Invalid polygon')
        return json.loads(to_geojson(MultiPolygon([poly for poly in ugcs_polygons])))

    def _get_polygon_from_url(self, cache: Cache, url):
        cacheKey = f'alert/polygon/{url}'
        if cache.has(cacheKey):
            rawData = cache.get(cacheKey)
            jsonData = json.loads(rawData)
            return shape(jsonData['geometry'])
        response = requests.get(
            url,
            headers={
                'Accept': 'application/geo+json',
                'User-Agent': 'weather-dashboard',
            }
        )
        if response.status_code != 200:
            raise ValueError('Failed to get polygon')
        res = response.json()
        if 'geometry' not in res or res['geometry'] is None:
            raise ValueError('Invalid polygon')
        if ('coordinates' not in res['geometry'] and (res['geometry']['type'] != "Polygon" or res['geometry']['type'] != "MultiPolygon")) \
                and (res['geometry']['type'] != "GeometryCollection"):
            print(res)
            print(url)
            raise ValueError('Invalid polygon')
        cache.set(cacheKey, response.content, datetime.timedelta(days=365))
        return shape(res['geometry'])

def _get_alerts_geojson(state):
    url = 'https://api.weather.gov/alerts/active?area={}&status=actual'.format(state)
    response = requests.get(
        url,
        headers={
            'Accept': 'application/geo+json',
            'User-Agent': 'weather-dashboard',
        }
    )
    return response.json()


def get_alerts(cache, state):
    state = state.upper()
    alertsJSON = _get_alerts_geojson(state)
    if 'type' not in alertsJSON or alertsJSON['type'] != 'FeatureCollection':
        print('Invalid GeoJSON FeatureCollection')
        return []

    if 'features' not in alertsJSON:
        print('No alerts found')
        return []

    alerts = []
    for feature in alertsJSON['features']:
        alerts.append(WXAlert(feature, state, cache))
    return alerts
