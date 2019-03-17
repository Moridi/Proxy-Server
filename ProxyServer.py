import json
import socket

class ProxyServer():
    def parseJsonFile(self, fileName):
        jsonFile = open(fileName, "r")
        contents = jsonFile.read()
        return json.loads(contents)

    def setupTcpConnection(self):
        MAX_CLIENT_NUMBER = 5

        proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxySocket.bind(('localhost', self.config["port"]))
        proxySocket.listen(MAX_CLIENT_NUMBER)
        return proxySocket

    def __init__(self, fileName):
        
        self.config = self.parseJsonFile(fileName)
        self.proxySocket = self.setupTcpConnection()

    def run(self):
        # while 1:
        # self.proxySocket.close()

        (clientsocket, address) = self.proxySocket.accept()

        # while True:
        data = clientsocket.recv(1024)
        # clientsocket.re
        print(data)
        if not data:
            print >>sys.stderr, 'no more data from', client_address
            # break

        self.proxySocket.close()

if (__name__ == "__main__"):
    proxyServer = ProxyServer("config.json")
    proxyServer.run()