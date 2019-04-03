import socket
import threading

from Logger import Logger
from Parser import Parser
from Cache import Cache
from MessageModifier import MessageModifier
from Restrictor import Restrictor
from Accountant import Accountant
from MessageInjector import MessageInjector

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
        proxySocket.listen(MAX_CLIENT_NUMBER)
        self.logger.log("Binding socket to port : " + str(self.config["port"])) 
        
        return proxySocket

    def prepareErrorMessage(self, fileName):
        openedFile = open(fileName, "r")
        formatedFile = ""

        for line in openedFile:
            formatedFile += line[ : -1] + "\r\n"

        self.errorMessage = bytes(formatedFile, 'utf-8')

        openedFile.close()

    def setupConfigObjects(self):
        self.messageModifier = MessageModifier(self.config["privacy"]["userAgent"],\
                self.config["privacy"]["enable"])

        self.logger = Logger(self.config["logging"]["logFile"],\
                self.config["logging"]["enable"])
                
        self.cache = Cache(self.config["caching"]["size"],\
                self.config["caching"]["enable"])

        self.restrictor = Restrictor(self.config["restriction"]["targets"],\
                self.config["restriction"]["enable"])

        self.accountant = Accountant(self.config["accounting"]["users"])

        self.messageInjector = MessageInjector(self.config["HTTPInjection"]["post"]["body"],\
                self.config["HTTPInjection"]["enable"])
        
        self.logger.log("Proxy launched")

    def __init__(self, fileName):
        self.config = Parser.parseJsonFile(fileName)
        self.prepareErrorMessage("errorMessage")
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
            httpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            httpSocket.connect((ipAddress, HTTP_PORT))
            self.logger.log("Proxy opening HTTP connection to server" + hostName +
                   " [" + ipAddress + "]...")
            
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

    def addToCache(self, data, isCachable, requestedUrl):
        age = self.isCachable(Parser.getPragmaFlag(data))

        if (age != 0):
            isCachable = True
            expiryDate = Parser.getExpiryDate(data)
            self.cache.createNewSlot(requestedUrl, expiryDate)

        if (isCachable):
            self.cache.addToCache(requestedUrl, data)

        return isCachable

    def prepareResponse(self, data, isCachable, requestedUrl):
        response = Parser.getResponseHeader(data)
        if (response != None):
            self.logger.log("Server sent response to proxy with headers:\n" + response)
            data = self.messageInjector.injectHttpResponse(data)
            response = Parser.getResponseHeader(data)
            self.logger.log("Proxy sent response to client with headers:\n" + response)

        return data

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
                self.logger.log("User doesn't have enough volume and " +
                        "proxy sent fallowing message to the client!" + self.errorMessage.decode())
                clientSocket.sendall(self.errorMessage)
                clientSocket.close()

    def sendDataToClient(self, httpSocket, clientSocket, clientAddress, requestedUrl):
        isCachable = False
        while True:
            try:
                data = httpSocket.recv(MAX_BUFFER_SIZE)
                if not data:
                    break

                isCachable = self.addToCache(data, isCachable, requestedUrl)
                data = self.prepareResponse(data, isCachable, requestedUrl)
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

                isCachable = self.addToCache(data, isCachable, requestedUrl)
                data = self.prepareResponse(data, isCachable, requestedUrl)
                self.checkUserVolume(data, clientSocket, clientAddress)
                clientSocket.sendall(data)
            except:
                return

    def sendHttpRequest(self, clientSocket, httpSocket, httpMessage):
        message = Parser.getRequestMessage(httpMessage)  
        self.logger.log("Proxy sent request to origin server with headers:\n" + message)

        try:
            httpSocket.sendall(bytes(message, 'utf-8'))
        except:
            pass

    def isRestricted(self, httpMessage):
        return self.restrictor.checkHostRestriction(Parser.getHostName(httpMessage))

    def responseFromCache(self, clientSocket, clientAddress, requestedUrl):
        HEADER_INDEX = 0

        cachedResponse = self.cache.getResponse(requestedUrl)

        header = Parser.getResponseHeader(cachedResponse[HEADER_INDEX])
        if (header != None):
            self.logger.log("Proxy sent response to client with headers: [From cache]\n" + header)

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

    def sendResponseToClient(self, httpMessage, clientSocket, clientAddress):
        requestedUrl = Parser.getUrl(httpMessage)
        self.prepareRequest(httpMessage)
        httpSocket = self.setupHttpConnection(httpMessage)

        if (self.cache.cacheHit(requestedUrl)):
            self.logger.log("Cache hit occurred!!")
            if (self.cache.isNotExpired(requestedUrl)):
                self.responseFromCache(clientSocket, clientAddress, requestedUrl)
            else:
                self.checkPacketValidity(httpSocket, clientSocket,\
                    clientAddress, requestedUrl, httpMessage)
        else:
            self.responseFromOriginServer(httpSocket, clientSocket,\
                    clientAddress, requestedUrl, httpMessage)

    def proxyThread(self, clientSocket, clientAddress):
        try:
            data = clientSocket.recv(MAX_BUFFER_SIZE)
            
            httpMessage = Parser.parseHttpMessage(data)
            self.logger.log("Client sent request to proxy with the fallowing headers:\n" +
                    data.decode())

            if (not self.isRestricted(httpMessage)):
                self.sendResponseToClient(httpMessage, clientSocket, clientAddress)
            else:
                self.logger.log("Request dropped!\n")
        except:
            pass
        clientSocket.close()

    def run(self):
        while True:
            (clientSocket, clientAddress) = self.proxySocket.accept()
            self.logger.log("Accepted a request from client!")
            self.logger.log("connect to " + str(clientAddress[IP_INDEX]) +
                   ":" + str(clientAddress[PORT_INDEX]))
            newThread = threading.Thread(target = self.proxyThread,
                    args=(clientSocket, clientAddress))
            newThread.setDaemon(True)
            newThread.start()