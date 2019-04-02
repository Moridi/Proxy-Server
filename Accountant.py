class Accountant(object):
    def __init__(self, users):
        self.accounts = {}

        for user in users:
            self.accounts[user["IP"]] = int(user["volume"])

    def decreaseUserVolume(self, ipAddress, contentLength):
        if (ipAddress in self.accounts):
            self.accounts[ipAddress] -= contentLength

    def hasEnoughVolume(self, ipAddress):
        if (ipAddress in self.accounts):
            return self.accounts[ipAddress] > 0
        return False

    def getVolume(self, ipAddress):
        return self.accounts[ipAddress]