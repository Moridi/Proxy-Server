import json
import socket

class Parser(object):
    @staticmethod
    def parseJsonFile(fileName):
        jsonFile = open(fileName, "r")
        contents = jsonFile.read()
        return json.loads(contents)   

    @staticmethod
    def parseHttpMessage(message):
        parsedData = []
        line = ""

        for character in message:
            if (chr(character) == '\r'):
                continue
            if (chr(character) == '\n'):
                parsedData.append(line)
                line = ""
                continue
            line += chr(character)

        return parsedData

class ProxyServer(object):
    def setupTcpConnection(self):
        MAX_CLIENT_NUMBER = 5

        proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxySocket.bind(('localhost', self.config["port"]))
        proxySocket.listen(MAX_CLIENT_NUMBER)
        return proxySocket

    def __init__(self, fileName):
        self.config = Parser.parseJsonFile(fileName)
        self.proxySocket = self.setupTcpConnection()
        self.HttpMessage = None

    def run(self):
        MAX_BUFFER_SIZE = 1024

        (clientsocket, address) = self.proxySocket.accept()
        data = clientsocket.recv(MAX_BUFFER_SIZE)
        if not data:
            print >>sys.stderr, 'no more data from', client_address

        self.httpMessage = Parser.parseHttpMessage(data)

        for x in self.httpMessage:
            print(x)

        self.proxySocket.close()

if (__name__ == "__main__"):
    proxyServer = ProxyServer("config.json")
    proxyServer.run()