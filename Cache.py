class Cache(object):
    def __init__(self, size, enable):
        self.size = int(size)
        self.space = [[]] * self.size
        self.enable = enable
        self.counter = int(0)

    def createNewSlot(self):
        self.counter = (self.counter + 1) % self.size
        self.space[self.counter] = []

    def addToCache(self, message):
        self.space[self.counter].append(message)