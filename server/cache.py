import datetime

import redis

class Cache:
    def __init__(self):
        self.cache = redis.StrictRedis(host='localhost', port=6379, db=0)

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value, expiration: datetime.timedelta = datetime.timedelta(hours=1)):
        return self.cache.set(key, value, expiration)

    def delete(self, key):
        return self.cache.delete(key)

    def keys(self):
        return self.cache.keys()
    
    def has(self, key):
        return self.cache.exists(key)
