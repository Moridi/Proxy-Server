from datetime import datetime

MESSAGE_INDEX = 1
EXPIRY_DATE_INDEX = 0

class Cache(object):
    def __init__(self, size, enable):
        self.size = int(size)
        self.space = {}
        self.enable = enable
        self.counter = int(0)

    def createNewSlot(self, requestedUrl, expiryDate):
        '''Storing format : URL -> (expiry date, [content])'''

        self.counter = (self.counter + 1) % self.size

        if (expiryDate == ""):
            self.space[requestedUrl] = (datetime.now(), [])
        else:
            self.space[requestedUrl] = (datetime.strptime(\
                    expiryDate, '%d %b %Y %H:%M:%S'), [])

    def addToCache(self, requestedUrl, message):
        if (requestedUrl in self.space):
            self.space[requestedUrl][MESSAGE_INDEX].append(message)

    def cacheHit(self, url):
        return url in self.space

    def getResponse(self, requestedUrl):
        if (requestedUrl in self.space):        
            return self.space[requestedUrl][MESSAGE_INDEX]
        return []

    def isNotExpired(self, requestedUrl):
        if (requestedUrl in self.space):
            return self.space[requestedUrl][EXPIRY_DATE_INDEX] > datetime.now()

    def getExpiryDate(self, requestedUrl):
        if (requestedUrl in self.space):
            return self.space[requestedUrl][EXPIRY_DATE_INDEX]
