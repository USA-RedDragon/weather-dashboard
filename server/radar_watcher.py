import calendar
import datetime
import logging
import threading
import time

from metpy.io import Level2File

from .cache import Cache
from .radar import get_radar_scan_time, extract_timestamp, get_specific_radar_scan, process

class RadarWatcher:
    def __init__(self, cache: Cache):
        self.timestamps = dict()
        self.threads = dict()
        self.cache = cache
        self.eventListeners = {}

    def _watch(self, station: str):
        while True:
            try:
                obj = get_radar_scan_time(station, 0)
                timestamp = extract_timestamp(obj, station)
                ts = calendar.timegm(timestamp.utctimetuple())
                if station not in self.timestamps:
                    self.timestamps[station] = ts
                elif self.timestamps[station] < ts:
                    self.timestamps[station] = ts
                    self._notify(station, ts)
            except Exception as e:
                logging.info(f"Error watching radar: {repr(e)}")
                print(f"Error watching radar: {repr(e)}")
            time.sleep(1)

    def is_watching(self, station: str):
        return station in self.threads

    def start(self, station: str):
        if station in self.threads:
            raise ValueError("Already watching this station")
        self.threads[station] = threading.Thread(target=self._watch, args=(station,), daemon=True)
        self.threads[station].start()

    def stop(self, station: str):
        if station not in self.threads:
            raise ValueError("Not watching this station")
        self.threads[station].join()
        del self.threads[station]

    def stop_all(self):
        for station in list(self.threads.keys()):
            self.stop(station)
        self.timestamps.clear()

    def add_event_listener(self, listener, station: str = '*'):
        if self.eventListeners.get(station) is not None:
            if listener in self.eventListeners[station]:
                return
            self.eventListeners[station].append(listener)
        else:
            self.eventListeners[station] = [listener]

    def remove_event_listener(self, listener, station: str = '*'):
        station = station.upper()
        if self.eventListeners.get(station) is not None:
            self.eventListeners[station].remove(listener)

    def _notify(self, station: str, timestamp: int):
        timeStart = time.monotonic()
        obj = get_specific_radar_scan(station, timestamp)
        f = Level2File(obj['Body'])
        logging.info(f"_notify download took {datetime.timedelta(seconds=time.monotonic() - timeStart)}")

        # Cache the 7 radar sweep elevations
        for i in range(7):
            if not self.cache.has(f"{station}/{i}/{timestamp}"):
                packed = process(f, i, timestamp)
                self.cache.set(f"{station}/{i}/{timestamp}", packed)
        # Then notify the listeners
        for listener in self.eventListeners.get(station, []) + self.eventListeners.get('*', []):
            try:
                listener(station, timestamp)
            except Exception as e:
                logging.info(f"Error notifying listener: {repr(e)}")
                print(f"Error notifying listener: {repr(e)}")
