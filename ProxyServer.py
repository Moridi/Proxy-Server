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
IP_INDEX = 0
PORT_INDEX = 1

class ProxyServer(object):
    def setupTcpConnection(self):
        self.logger.log("Creating server socket...")
        proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxySocket.bind(('localhost', self.config["port"]))
        self.logger.log("Binding socket to port : " + str(self.config["port"])) 
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
        
        self.logger.log("Proxy launched")

    def __init__(self, fileName):
        self.config = Parser.parseJsonFile(fileName)
        self.setupConfigObjects()
        self.proxySocket = self.setupTcpConnection()

    def prepareRequest(self, httpMessage):
        self.messageModifier.changeHttpVersion(httpMessage)
        self.messageModifier.changeUrl(httpMessage)
        self.messageModifier.removeProxyHeader(httpMessage)
        self.messageModifier.changeUserAgent(httpMessage)

    def setupHttpConnection(self, httpMessage):
        URL_PART = HOST_NAME_LINE = FIRST_CHAR = 1
        HTTP_PORT = 80

        try:
            hostName = httpMessage[HOST_NAME_LINE][URL_PART][FIRST_CHAR : ]
            ipAddress = socket.gethostbyname(hostName)
            # httpSocket.settimeout(CONNECTION_TIMEOUT)
            httpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            httpSocket.connect((ipAddress, HTTP_PORT))
            self.logger.log("Proxy opening connection to server" + hostName + " [" + ipAddress + "]...")
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

    def prepareResponse(self, data, isCachable, requestedUrl):
        self.logger.log(Parser.getResponseLine(data))
        age = self.isCachable(Parser.getPragmaFlag(data)) 

        if (age != 0):
            isCachable = True
            expiryDate = Parser.getExpiryDate(data)
            self.cache.createNewSlot(requestedUrl, expiryDate)

        if (isCachable):
            self.cache.addToCache(requestedUrl, data)

        self.messageModifier.injectHttpResponse(data)

        return isCachable

    def isNotModified(self, data, isCachable, requestedUrl):
        NOT_MODIFIED = "304"
        
        self.logger.log(Parser.getResponseLine(data))
        responseLine = Parser.getResponseLine(data)
        if (NOT_MODIFIED in responseLine):
            return True
        else:
            return False

    def checkUserVolume(self, message, clientSocket, clientAddress):
        IP_INDEX = 0
        volume = Parser.getHeaderValue(message, "Content-Length")

        if (volume != ""):
            self.accountant.decreaseUserVolume(clientAddress[IP_INDEX], int(volume))

            if (not self.accountant.hasEnoughVolume(clientAddress[IP_INDEX])):
                clientSocket.close()

    def sendDataToClient(self, httpSocket, clientSocket, clientAddress, requestedUrl):
        isCachable = False
        while True:
            try:
                data = httpSocket.recv(MAX_BUFFER_SIZE)
                if not data:
                    break

                isCachable = self.prepareResponse(data, isCachable, requestedUrl)
                self.checkUserVolume(data, clientSocket, clientAddress)
                clientSocket.sendall(data)
            except:
                break

    def sendExpiredRequestToClient(self, httpSocket, clientSocket, clientAddress, requestedUrl):
        isCachable = False
        while True:
            try:
                data = httpSocket.recv(MAX_BUFFER_SIZE)
                if not data:
                    return

                if (self.isNotModified(data, isCachable, requestedUrl)):
                    self.responseFromCache(clientSocket, clientAddress, requestedUrl)
                    return

                isCachable = self.prepareResponse(data, isCachable, requestedUrl)
                self.checkUserVolume(data, clientSocket, clientAddress)
                clientSocket.sendall(data)
            except:
                return

    def sendHttpRequest(self, clientSocket, httpSocket, httpMessage):
        message = Parser.getRequestMessage(httpMessage)  
        self.logger.log("Proxy sent request to server with headers:")
        self.logger.log(message)

        try:
            httpSocket.sendall(bytes(message, 'utf-8'))
        except:
            pass

    def isRestricted(self, httpMessage):
        return self.smtpHandler.checkHostRestriction(Parser.getHostName(httpMessage))

    def responseFromCache(self, clientSocket, clientAddress, requestedUrl):
        cachedResponse = self.cache.getResponse(requestedUrl)

        for partOfResponse in cachedResponse:
            try:
                self.checkUserVolume(partOfResponse, clientSocket, clientAddress)
                clientSocket.sendall(partOfResponse)
            except:
                break

    def responseFromOriginServer(self, httpSocket, clientSocket,\
            clientAddress, requestedUrl, httpMessage):
        self.sendHttpRequest(clientSocket, httpSocket, httpMessage)
        self.sendDataToClient(httpSocket, clientSocket, clientAddress, requestedUrl)

    def checkPacketValidity(self, httpSocket, clientSocket,\
            clientAddress, requestedUrl, httpMessage):
        '''This method is called when the requested
                packet is cached but it's been expired '''

        self.messageModifier.changeIfModifiedSinceHeader(\
                self.cache.getExpiryDate(requestedUrl), httpMessage)

        self.sendHttpRequest(clientSocket, httpSocket, httpMessage)
        self.sendExpiredRequestToClient(httpSocket, clientSocket, clientAddress, requestedUrl)

    def proxyThread(self, clientSocket, clientAddress):
        data = clientSocket.recv(MAX_BUFFER_SIZE)
        
        httpMessage = Parser.parseHttpMessage(data)
        self.logger.log("Client sent request to proxy with the fallowing headers:")
        self.logger.log(data.decode())

        if (not self.isRestricted(httpMessage)):
            requestedUrl = Parser.getUrl(httpMessage)
            self.prepareRequest(httpMessage)
            httpSocket = self.setupHttpConnection(httpMessage)

            if (self.cache.cacheHit(requestedUrl)):
                if (self.cache.isNotExpired(requestedUrl)):
                    self.responseFromCache(clientSocket, clientAddress, requestedUrl)
                else:
                    self.checkPacketValidity(httpSocket, clientSocket,\
                        clientAddress, requestedUrl, httpMessage)
            else:
                self.responseFromOriginServer(httpSocket, clientSocket,\
                        clientAddress, requestedUrl, httpMessage)

        clientSocket.close()

    def run(self):
        while True:
            self.logger.log("Listening for incoming requests...\n")
            (clientSocket, clientAddress) = self.proxySocket.accept()
            self.logger.log("Accepted a request from client!")
            self.logger.log("connect to " + str(clientAddress[IP_INDEX]) + ":" + str(clientAddress[PORT_INDEX]))
            newThread = threading.Thread(target = self.proxyThread, args=(clientSocket, clientAddress))
            newThread.setDaemon(True)
            newThread.start()