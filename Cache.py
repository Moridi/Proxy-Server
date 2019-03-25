from datetime import datetime

EXPIRY_DATE_INDEX = 0
MESSAGE_INDEX = 1

class Cache(object):
    def __init__(self, size, enable):
        self.size = int(size)
        self.space = [(None, [])] * self.size
        self.enable = enable
        self.counter = int(0)

    def createNewSlot(self, expiryDate):
        self.counter = (self.counter + 1) % self.size

        if (expiryDate == ""):
            self.space[self.counter] = (datetime.now(), [])
        else:
            self.space[self.counter] = (datetime.strptime(expiryDate, '%d %b %Y %H:%M:%S'), [])

    def addToCache(self, message):
        self.space[self.counter][MESSAGE_INDEX].append(message)