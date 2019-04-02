import datetime

class Logger(object):
    def __init__(self, fileName, enable):
        self.fileName = fileName
        self.enable = enable

    def log(self, message):
        if (self.enable and message != None):
            self.openedFile = open(self.fileName, "a+")
            self.openedFile.write(str(datetime.datetime.now()) + " : " + message + "\n")
            self.openedFile.close()