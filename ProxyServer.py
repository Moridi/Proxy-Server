import socket
import threading

from Parser import Parser

MAX_BUFFER_SIZE = 1024

class ProxyServer(object):
    def setupTcpConnection(self):
        MAX_CLIENT_NUMBER = 300

        proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxySocket.bind(('localhost', self.config["port"]))
        proxySocket.listen(MAX_CLIENT_NUMBER)
        return proxySocket

    def __init__(self, fileName):
        self.config = Parser.parseJsonFile(fileName)
        self.proxySocket = self.setupTcpConnection()

    def changeHttpVersion(self, httpMessage):
        REQUEST_LINE = 0
        FIRST_PART = 0
        HTTP_VERSION_PART = 1
        HTTP_VERSION = "HTTP/1.0"

        httpVersionIndex = httpMessage[REQUEST_LINE][HTTP_VERSION_PART].find(" ") + 1

        httpMessage[REQUEST_LINE] = (\
                httpMessage[REQUEST_LINE][FIRST_PART],\
                httpMessage[REQUEST_LINE][HTTP_VERSION_PART][ : httpVersionIndex] +\
                HTTP_VERSION + httpMessage[REQUEST_LINE][HTTP_VERSION_PART][\
                httpVersionIndex + len(HTTP_VERSION) : ])

    def changeUrl(self, httpMessage):
        REQUEST_LINE = 0
        HOST_NAME_LINE = 1
        FIRST_PART = 0
        URL_PART = 1
        HTTP_PART = "http:/"

        spaceIndex = httpMessage[REQUEST_LINE][URL_PART].find(" ")

        httpMessage[REQUEST_LINE] = (httpMessage[REQUEST_LINE][FIRST_PART],\
                httpMessage[REQUEST_LINE][URL_PART][len(HTTP_PART) +\
                len(httpMessage[HOST_NAME_LINE][URL_PART]) : ])

    def getProxyConnectionIndex(self, httpMessage):
        PROXY_CONNECTION = "Proxy-Connection"
        FIELD_PART = 0

        index = [i for i, x in enumerate(httpMessage) if(x[FIELD_PART] == PROXY_CONNECTION)]
        if (len(index) == 0):
            return -1
        return index[0]

    def removeProxyHeader(self, httpMessage):
        index = self.getProxyConnectionIndex(httpMessage)
        httpMessage.pop(index)

    def prepareRequest(self, httpMessage):
        self.changeHttpVersion(httpMessage)
        self.changeUrl(httpMessage)
        self.removeProxyHeader(httpMessage)

    def setupHttpConnection(self, httpMessage):
        URL_PART = HOST_NAME_LINE = FIRST_CHAR = 1
        HTTP_PORT = 80

        ipAddress = socket.gethostbyname(httpMessage[HOST_NAME_LINE][URL_PART][FIRST_CHAR : ])

        httpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        httpSocket.connect((ipAddress, HTTP_PORT))
        
        return httpSocket

    def getRequestMessage(self, httpMessage):
        message = ""
        for i, x in enumerate(httpMessage):
            if (i == 0):
                message += x[0] + " " + x[1] + "\r\n"                
            else:
                message += x[0] + ":" + x[1] + "\r\n"
        
        message += "\r\n"

        return message

    def sendHttpRequest(self, clientSocket, httpSocket, httpMessage):
        message = self.getRequestMessage(httpMessage)     

        httpSocket.sendall(bytes(message, 'utf-8'))

        while True:
            data = httpSocket.recv(1024)
            if not data:
                break
            print(str(data))
            clientSocket.sendall(data)

    def proxyThread(self, clientSocket, clientAddress):
            data = clientSocket.recv(MAX_BUFFER_SIZE)
            
            httpMessage = Parser.parseHttpMessage(data)
            self.prepareRequest(httpMessage)

            httpSocket = self.setupHttpConnection(httpMessage)
            self.sendHttpRequest(clientSocket, httpSocket, httpMessage)

    def run(self):
        while True:
            # Establish the connection
            (clientSocket, clientAddress) = self.proxySocket.accept()
            d = threading.Thread(target = self.proxyThread, args=(clientSocket, clientAddress))
            d.setDaemon(True)
            d.start()