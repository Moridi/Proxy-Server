from datetime import datetime

EXPIRY_DATE_INDEX = 0
MESSAGE_INDEX = 1
ACCESS_TIME_INDEX = 2

class Cache(object):
    def __init__(self, size, enable):
        self.size = int(size)
        self.space = {}
        self.enable = enable

    def deleteLruRecord(self):
        minUrl = ""
        minDate = datetime.max

        for key, value in self.space.items():
            if (value[ACCESS_TIME_INDEX] < minDate):
                minUrl = key
                minDate = value[ACCESS_TIME_INDEX]

        if (minUrl != ""):
            del self.space[minUrl]

    def createNewSlot(self, requestedUrl, expiryDate):
        '''Storing format : URL -> (expiry date, [content], access time)'''

        if (len(self.space) == self.size):
            self.deleteLruRecord()

        if (expiryDate == ""):
            self.space[requestedUrl] = (datetime.now(), [], datetime.now())
        else:
            self.space[requestedUrl] = (datetime.strptime(\
                    expiryDate, '%d %b %Y %H:%M:%S'), [], datetime.now())

    def addToCache(self, requestedUrl, message):
        if (requestedUrl in self.space):
            self.space[requestedUrl][MESSAGE_INDEX].append(message)

    def cacheHit(self, url):
        return url in self.space

    def getResponse(self, requestedUrl):
        if (requestedUrl in self.space):
            self.space[requestedUrl] = (self.space[requestedUrl][EXPIRY_DATE_INDEX], 
                    self.space[requestedUrl][MESSAGE_INDEX], 
                    datetime.now())

            return self.space[requestedUrl][MESSAGE_INDEX]
        return []

    def isNotExpired(self, requestedUrl):
        if (requestedUrl in self.space):
            return self.space[requestedUrl][EXPIRY_DATE_INDEX] > datetime.now()

    def getExpiryDate(self, requestedUrl):
        if (requestedUrl in self.space):
            return self.space[requestedUrl][EXPIRY_DATE_INDEX]
