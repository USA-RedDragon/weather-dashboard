import datetime

import redis

class Cache:
    def __init__(self):
        self.cache = redis.StrictRedis(host='localhost', port=6379, db=0)

    def get(self, key: str):
        return self.cache.get(key.upper())

    def set(self, key: str, value, expiration: datetime.timedelta = datetime.timedelta(hours=1)):
        return self.cache.set(key.upper(), value, expiration)

    def delete(self, key: str):
        return self.cache.delete(key.upper())

    def keys(self):
        return self.cache.keys()
    
    def has(self, key: str):
        return self.cache.exists(key.upper())
