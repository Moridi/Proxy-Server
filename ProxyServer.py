import json
import socket

class Parser(object):
    @staticmethod
    def parseJsonFile(fileName):
        jsonFile = open(fileName, "r")
        contents = jsonFile.read()
        return json.loads(contents)   

    @staticmethod
    def tokenizeByLine(message):
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


    @staticmethod
    def parseHttpMessage(message):
        DELIMITER = ":"
        REQUEST_DELIMITER = " "

        lines = Parser.tokenizeByLine(message)
        parsedData = []
        for index, line in enumerate(lines):
            if (index == 0):
                delmiterIndex = line.find(REQUEST_DELIMITER)
                parsedData.append((line[ : delmiterIndex],\
                        line[delmiterIndex + 1 : ]))
                continue

            delmiterIndex = line.find(DELIMITER)
            parsedData.append((line[ : delmiterIndex],\
                    line[delmiterIndex + 1 : ]))          

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

    def changeHttpVersion(self):
        httpVersionIndex = self.httpMessage[0][1].find("HTTP/1.")
        self.httpMessage[0] = (self.httpMessage[0][0],\
                self.httpMessage[0][1][ : httpVersionIndex] +\
                "HTTP/1.0" + self.httpMessage[0][1][httpVersionIndex + 8 : ])

    def changeUrl(self):
        spaceIndex = self.httpMessage[0][1].find(" ")

        self.httpMessage[0] = (self.httpMessage[0][0], self.httpMessage[0][1][6 + len(self.httpMessage[1][1]) : ])

    def prepareRequest(self):
        self.changeHttpVersion()
        self.changeUrl()

    def run(self):
        MAX_BUFFER_SIZE = 1024

        (clientsocket, address) = self.proxySocket.accept()
        data = clientsocket.recv(MAX_BUFFER_SIZE)
        self.httpMessage = Parser.parseHttpMessage(data)
        self.prepareRequest()

        for x in self.httpMessage:
            print(x)

        self.proxySocket.close()

if (__name__ == "__main__"):
    proxyServer = ProxyServer("config.json")
    proxyServer.run()