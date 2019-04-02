class SmtpHandler(object):
    def __init__(self, targets, enable):
        self.enable = enable
        self.targets = {}
        for target in targets:
            self.targets[target["URL"]] = target["notify"]
    
    def sendAlertMail(self):
        return None

    def checkHostRestriction(self, host):
        if (host in self.targets):
            if (self.targets[host] == "true"):
                self.sendAlertMail()
            return True
        return False