import socket
import threading

from Logger import Logger
from Parser import Parser
from Cache import Cache

MAX_BUFFER_SIZE = 1024
CONNECTION_TIMEOUT = 10
MAX_CLIENT_NUMBER = 300

class ProxyServer(object):
    def setupTcpConnection(self):

        proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxySocket.bind(('localhost', self.config["port"]))
        proxySocket.listen(MAX_CLIENT_NUMBER)
        return proxySocket

    def __init__(self, fileName):
        self.config = Parser.parseJsonFile(fileName)
        self.proxySocket = self.setupTcpConnection()
        self.logger = Logger(self.config["logging"]["logFile"],\
                self.config["logging"]["enable"])
                
        self.cache = Cache(self.config["caching"]["size"],\
                self.config["caching"]["enable"])

    def changeHttpVersion(self, httpMessage):
        REQUEST_LINE = 0
        FIRST_PART = 0
        HTTP_VERSION_PART = 1
        HTTP_VERSION = "HTTP/1.0"

        try:
            httpVersionIndex = httpMessage[REQUEST_LINE][HTTP_VERSION_PART].find(" ") + 1
            httpMessage[REQUEST_LINE] = (\
                    httpMessage[REQUEST_LINE][FIRST_PART],\
                    httpMessage[REQUEST_LINE][HTTP_VERSION_PART][ : httpVersionIndex] +\
                    HTTP_VERSION + httpMessage[REQUEST_LINE][HTTP_VERSION_PART][\
                    httpVersionIndex + len(HTTP_VERSION) : ])
        except:
            pass

    def changeUrl(self, httpMessage):
        REQUEST_LINE = 0
        HOST_NAME_LINE = 1
        FIRST_PART = 0
        URL_PART = 1
        HTTP_PART = "http:/"

        try:
            spaceIndex = httpMessage[REQUEST_LINE][URL_PART].find(" ")
            httpMessage[REQUEST_LINE] = (httpMessage[REQUEST_LINE][FIRST_PART],\
                    httpMessage[REQUEST_LINE][URL_PART][len(HTTP_PART) +\
                    len(httpMessage[HOST_NAME_LINE][URL_PART]) : ])
        except:
            pass

    def getProxyConnectionIndex(self, httpMessage):
        PROXY_CONNECTION = "Proxy-Connection"
        FIELD_PART = 0

        index = [i for i, x in enumerate(httpMessage) if(x[FIELD_PART] == PROXY_CONNECTION)]
        if (len(index) == 0):
            return -1
        return index[0]

    def removeProxyHeader(self, httpMessage):
        index = self.getProxyConnectionIndex(httpMessage)
        try:
            httpMessage.pop(index)
        except:
            pass

    def prepareRequest(self, httpMessage):
        self.changeHttpVersion(httpMessage)
        self.changeUrl(httpMessage)
        self.removeProxyHeader(httpMessage)

    def setupHttpConnection(self, httpMessage):
        URL_PART = HOST_NAME_LINE = FIRST_CHAR = 1
        HTTP_PORT = 80

        try:
            ipAddress = socket.gethostbyname(httpMessage[HOST_NAME_LINE][URL_PART][FIRST_CHAR : ])
            # httpSocket.settimeout(CONNECTION_TIMEOUT)
            httpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            httpSocket.connect((ipAddress, HTTP_PORT))
            return httpSocket
        except:
            pass

    def getRequestMessage(self, httpMessage):
        message = ""
        for i, x in enumerate(httpMessage):
            if (i == 0):
                message += x[0] + " " + x[1] + "\r\n"                
            else:
                message += x[0] + ":" + x[1] + "\r\n"
        
        message += "\r\n"

        return message
    
    def isCachable(self, message):
        MAX_AGE = "max-age="
        NOT_FOUND = -1

        ageIndex = message.find(MAX_AGE)
        if (ageIndex != NOT_FOUND):
            return int(message[ageIndex + len(MAX_AGE) : ])
        return 0

    def sendDataToClient(self, httpSocket, clientSocket):
        isCachable = False
        while True:
            try:
                data = httpSocket.recv(MAX_BUFFER_SIZE)
                if not data:
                    break

                self.logger.serverLog(Parser.getResponseLine(data))
                age = self.isCachable(Parser.getPragmaFlag(data)) 

                if (age != 0):
                    isCachable = True
                    expiryDate = Parser.getExpiryDate(data)
                    self.cache.createNewSlot(expiryDate)

                if (isCachable):
                    self.cache.addToCache(data)

                clientSocket.sendall(data)
            except:
                break

    def sendHttpRequest(self, clientSocket, httpSocket, httpMessage):
        REQUEST_LINE = 0

        message = self.getRequestMessage(httpMessage)     
        
        try:
            self.logger.clientLog(httpMessage[REQUEST_LINE][0] +\
                    " " + httpMessage[REQUEST_LINE][1])
            httpSocket.sendall(bytes(message, 'utf-8'))
        except:
            pass

        self.sendDataToClient(httpSocket, clientSocket)

    def proxyThread(self, clientSocket, clientAddress):
            data = clientSocket.recv(MAX_BUFFER_SIZE)
            
            httpMessage = Parser.parseHttpMessage(data)
            self.prepareRequest(httpMessage)

            httpSocket = self.setupHttpConnection(httpMessage)
            self.sendHttpRequest(clientSocket, httpSocket, httpMessage)

    def run(self):
        while True:
            (clientSocket, clientAddress) = self.proxySocket.accept()
            newThread = threading.Thread(target = self.proxyThread, args=(clientSocket, clientAddress))
            newThread.setDaemon(True)
            newThread.start()