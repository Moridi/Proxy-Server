import socket
import threading

from Logger import Logger
from Parser import Parser
from Cache import Cache
from MessageModifier import MessageModifier
from SmtpHandler import SmtpHandler
from Accountant import Accountant

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

    def setupConfigObjects(self):
        self.messageModifier = MessageModifier(self.config["privacy"]["userAgent"],\
                self.config["privacy"]["enable"])

        self.logger = Logger(self.config["logging"]["logFile"],\
                self.config["logging"]["enable"])
                
        self.cache = Cache(self.config["caching"]["size"],\
                self.config["caching"]["enable"])

        self.smtpHandler = SmtpHandler(self.config["restriction"]["targets"],\
                self.config["restriction"]["enable"])

        self.accountant = Accountant(self.config["accounting"]["users"])


    def __init__(self, fileName):
        self.config = Parser.parseJsonFile(fileName)
        self.proxySocket = self.setupTcpConnection()
        self.setupConfigObjects()

    def prepareRequest(self, httpMessage):
        self.messageModifier.changeHttpVersion(httpMessage)
        self.messageModifier.changeUrl(httpMessage)
        self.messageModifier.removeProxyHeader(httpMessage)
        self.messageModifier.changeUserAgent(httpMessage)

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
    
    def isCachable(self, message):
        MAX_AGE = "max-age="
        NOT_FOUND = -1

        ageIndex = message.find(MAX_AGE)
        if (ageIndex != NOT_FOUND):
            return int(message[ageIndex + len(MAX_AGE) : ])
        return 0

    def prepareResponse(self, data, isCachable):
        self.logger.serverLog(Parser.getResponseLine(data))
        age = self.isCachable(Parser.getPragmaFlag(data)) 

        if (age != 0):
            isCachable = True
            expiryDate = Parser.getExpiryDate(data)
            self.cache.createNewSlot(expiryDate)

        if (isCachable):
            self.cache.addToCache(data)

        self.messageModifier.injectHttpResponse(data)

        return isCachable

    def checkUserVolume(self, message, clientSocket, clientAddress):
        IP_INDEX = 0
        volume = Parser.getHeaderValue(message, "Content-Length")

        if (volume != ""):
            self.accountant.decreaseUserVolume(clientAddress[IP_INDEX], int(volume))

            if (not self.accountant.hasEnoughVolume(clientAddress[IP_INDEX])):
                clientSocket.close()

    def sendDataToClient(self, httpSocket, clientSocket, clientAddress):
        isCachable = False
        while True:
            try:
                data = httpSocket.recv(MAX_BUFFER_SIZE)
                if not data:
                    break

                isCachable = self.prepareResponse(data, isCachable)
                self.checkUserVolume(data, clientSocket, clientAddress)
                clientSocket.sendall(data)
            except:
                break

    def sendHttpRequest(self, clientSocket, httpSocket, httpMessage):
        REQUEST_LINE = 0

        message = Parser.getRequestMessage(httpMessage)     

        try:
            self.logger.clientLog(httpMessage[REQUEST_LINE][0] +\
                    " " + httpMessage[REQUEST_LINE][1])
            httpSocket.sendall(bytes(message, 'utf-8'))
        except:
            pass


    def isRestricted(self, httpMessage):
        return self.smtpHandler.checkHostRestriction(Parser.getHostName(httpMessage))

    def proxyThread(self, clientSocket, clientAddress):
            data = clientSocket.recv(MAX_BUFFER_SIZE)
            
            httpMessage = Parser.parseHttpMessage(data)

            if (not self.isRestricted(httpMessage)):
                self.prepareRequest(httpMessage)

                httpSocket = self.setupHttpConnection(httpMessage)
                self.sendHttpRequest(clientSocket, httpSocket, httpMessage)
                self.sendDataToClient(httpSocket, clientSocket, clientAddress)

            clientSocket.close()

    def run(self):
        while True:
            (clientSocket, clientAddress) = self.proxySocket.accept()
            newThread = threading.Thread(target = self.proxyThread, args=(clientSocket, clientAddress))
            newThread.setDaemon(True)
            newThread.start()