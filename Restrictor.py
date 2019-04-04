from socket import *
import base64
import time

MAX_BUFFER_SIZE = 1024
MAIL_SERVER = "mail.ut.ac.ir"

class Restrictor(object):
    def __init__(self, targets, enable):
        self.enable = enable
        self.targets = {}
        for target in targets:
            self.targets[target["URL"]] = target["notify"]
            self.targets["www." + target["URL"]] = target["notify"]
    
    def getClientSocket(self):
        MAIL_SERVER_PORT = 25

        mailserver = (MAIL_SERVER, MAIL_SERVER_PORT)
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.clientSocket.connect(mailserver)
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)

        if recvMessage[ : 3] != '220':
            print('220 reply not received from server.')

    def sendHeloCommand(self):
        heloCommand = 'HELO ' + MAIL_SERVER + '\r\n'
        self.clientSocket.send(heloCommand.encode())
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)

        if recvMessage[ : 3] != '250':
            print('250 reply not received from server.')

    def sendAuthCommand(self):
        # It is wrong username and password
        username = "xxxxxx\n"
        password = "xxxxxx"
        base64_str = ("\x00" + username + "\x00" + password).encode()
        base64_str = base64.b64encode(base64_str)
        authMessage = "AUTH LOGIN ".encode() + base64_str + "\r\n".encode()
        self.clientSocket.send(authMessage)
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)

    def sendMailFromCommand(self):
        mailFrom = "MAIL FROM:<moridi@ut.ac.ir>\r\n"
        self.clientSocket.send(mailFrom.encode())
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)

    def sendRcptToCommand(self):
        rcptTo = "RCPT TO:<ali.edalat@ut.ac.ir>\r\n"
        self.clientSocket.send(rcptTo.encode())
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)

    def sendDataCommand(self):
        data = "DATA\r\n"
        self.clientSocket.send(data.encode())
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)

    def sendMailContent(self):
        msg = "\r\n" + message
        endmsg = "\r\n.\r\n"

        subject = "Subject: Alert\r\n\r\n" 
        self.clientSocket.send(subject.encode())
        date = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        date = date + "\r\n\r\n"
        self.clientSocket.send(date.encode())
        self.clientSocket.send(msg.encode())
        self.clientSocket.send(endmsg.encode())
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)

    def sendQuitCommand(self):
        quit = "QUIT\r\n"
        self.clientSocket.send(quit.encode())
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)
        self.clientSocket.close()

    def sendAlertMail(self, host, message):
        if (self.targets[host] == "true"):
            self.getClientSocket()
            self.sendHeloCommand()
            self.sendAuthCommand()
            self.sendMailFromCommand()
            self.sendRcptToCommand()
            self.sendDataCommand()
            self.sendMailContent(message)
            self.sendQuitCommand()

    def checkHostRestriction(self, host):
        if (host in self.targets):
            return True
        return False