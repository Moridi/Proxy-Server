import socket

from Parser import Parser

class ProxyServer(object):
    def setupTcpConnection(self):
        MAX_CLIENT_NUMBER = 5

        proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxySocket.bind(('localhost', self.config["port"]))
        proxySocket.listen(MAX_CLIENT_NUMBER)
        return proxySocket

    def __init__(self, fileName):
        self.config = Parser.parseJsonFile(fileName)
        self.proxySocket = self.setupTcpConnection()

    def changeHttpVersion(self):
        REQUEST_LINE = 0
        FIRST_PART = 0
        HTTP_VERSION_PART = 1
        HTTP_VERSION = "HTTP/1.0"

        httpVersionIndex = self.httpMessage[REQUEST_LINE][HTTP_VERSION_PART].find(" ") + 1

        self.httpMessage[REQUEST_LINE] = (\
                self.httpMessage[REQUEST_LINE][FIRST_PART],\
                self.httpMessage[REQUEST_LINE][HTTP_VERSION_PART][ : httpVersionIndex] +\
                HTTP_VERSION + self.httpMessage[REQUEST_LINE][HTTP_VERSION_PART][\
                httpVersionIndex + len(HTTP_VERSION) : ])

    def changeUrl(self):
        REQUEST_LINE = 0
        HOST_NAME_LINE = 1
        FIRST_PART = 0
        URL_PART = 1
        HTTP_PART = "http:/"

        spaceIndex = self.httpMessage[REQUEST_LINE][URL_PART].find(" ")

        self.httpMessage[REQUEST_LINE] = (self.httpMessage[REQUEST_LINE][FIRST_PART],\
                self.httpMessage[REQUEST_LINE][URL_PART][len(HTTP_PART) +\
                len(self.httpMessage[HOST_NAME_LINE][URL_PART]) : ])

    def getProxyConnectionIndex(self):
        PROXY_CONNECTION = "Proxy-Connection"
        FIELD_PART = 0

        index = [i for i, x in enumerate(self.httpMessage) if(x[FIELD_PART] == PROXY_CONNECTION)]
        if (len(index) == 0):
            return -1
        return index[0]

    def removeProxyHeader(self):
        index = self.getProxyConnectionIndex()
        self.httpMessage.pop(index)

    def prepareRequest(self):
        self.changeHttpVersion()
        self.changeUrl()
        self.removeProxyHeader()

    def setupHttpConnection(self):
        URL_PART = HOST_NAME_LINE = FIRST_CHAR = 1
        HTTP_PORT = 80

        ipAddress = socket.gethostbyname(self.httpMessage[HOST_NAME_LINE][URL_PART][FIRST_CHAR : ])

        httpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        httpSocket.connect((ipAddress, HTTP_PORT))
        
        return httpSocket

    def getRequestMessage(self):
        message = ""
        for i, x in enumerate(self.httpMessage):
            if (i == 0):
                message += x[0] + " " + x[1] + "\r\n"                
            else:
                message += x[0] + ":" + x[1] + "\r\n"
        
        message += "\r\n"

        return message

    def sendHttpRequest(self):
        message = self.getRequestMessage()        

        self.httpSocket.sendall(bytes(message, 'utf-8'))

        while True:
            data = self.httpSocket.recv(1024)
            if not data:
                break
            print(str(data))
            self.clientsocket.sendall(data)

    def run(self):
        MAX_BUFFER_SIZE = 1024

        (self.clientsocket, address) = self.proxySocket.accept()

        data = self.clientsocket.recv(MAX_BUFFER_SIZE)
        
        self.httpMessage = Parser.parseHttpMessage(data)
        self.prepareRequest()

        self.httpSocket = self.setupHttpConnection()
        self.sendHttpRequest()
        self.proxySocket.close()