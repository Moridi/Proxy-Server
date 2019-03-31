import datetime

class Logger(object):
    def __init__(self, fileName, enable):
        self.fileName = fileName
        self.enable = enable

    def clientLog(self, message):
        if (self.enable):
            self.openedFile = open(self.fileName, "a+")
            self.openedFile.write(str(datetime.datetime.now()) + " : Clinet : " + message + "\n")
            self.openedFile.close()

    def serverLog(self, message):
        if (self.enable and message != None):
            self.openedFile = open(self.fileName, "a+")
            self.openedFile.write(str(datetime.datetime.now()) + " : Server : " + message + "\n")
            self.openedFile.close()