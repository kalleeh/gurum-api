
class Cache:
    """
    Used as a cache for calls within threads.
    A single instance of this class is passed into all threads to act
    as a cache.
    """

    def __init__(self):
        self._stash = {}

    def check(self, key):
        try:
            return self._stash[key]
        except KeyError:
            return None

    def add(self, key, value):
        self._stash[key] = value
