from Parser import Parser

class MessageInjector(object):
    def __init__(self, message, enable):
        self.enable = enable
        self.message = message

    def injectHttpResponse(self, httpMessage):
        if (self.enable):
            return Parser.getBody(httpMessage, self.message)
        return httpMessage