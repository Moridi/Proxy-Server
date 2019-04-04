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
    
    def sendMessage(self, message):
        self.clientSocket.send(message.encode())
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)
        recvMessage = recvMessage.decode()

        if (recvMessage[ : 3] != "250"):
            print('250 reply not received from server.')

    def getClientSocket(self):
        mailserver = ("mail.ut.ac.ir", 25)
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.clientSocket.connect(mailserver)
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)
        recvMessage = recvMessage.decode()

        if recvMessage[:3] != '220':
            print('220 reply not received from server.')

    def sendHeloCommand(self):
        heloCommand = 'HELO ' + MAIL_SERVER + '\r\n'
        self.sendMessage(heloCommand)

    def sendAuthValue(self, message):
        base64_str = message.encode()
        authMessage = base64.b64encode(base64_str)
        self.clientSocket.send(authMessage)
        self.clientSocket.send("\r\n".encode())
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)
        recvMessage = recvMessage.decode()
        return recvMessage[ : 3]

    def sendAuthCommand(self):
        self.clientSocket.send("AUTH LOGIN\r\n".encode())
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)
        recvMessage = recvMessage.decode()

        if (recvMessage[0 : 3] != '334'):
            print('334 reply not received from server. [AUTH LOGIN]')
        
        username = "xxxxxx\n"
        password = "xxxxxx"
        
        returnCode = self.sendAuthValue(username)
        returnCode = self.sendAuthValue(password)
        if (returnCode != "235"):
            print('Authentication failed.')

    def sendMailFromCommand(self):
        mailFrom = "MAIL FROM: <m.moridi@ut.ac.ir>\r\n"
        self.sendMessage(mailFrom)

    def sendRcptToCommand(self):
        rcptTo = "RCPT TO: <ali.edalat@ut.ac.ir>\r\n"
        self.sendMessage(rcptTo)

    def sendDataCommand(self):
        data = "DATA\r\n"
        self.clientSocket.send(data.encode())
        recvMessage = self.clientSocket.recv(MAX_BUFFER_SIZE)
        recvMessage = recvMessage.decode()

    def sendMailContent(self, message):
        msg = "\r\n" + message
        endmsg = "\r\n.\r\n"

        subject = "Subject: Alert\r\n\r\n" 
        self.clientSocket.send(subject.encode())
        date = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        date = date + "\r\n\r\n"
        self.clientSocket.send(date.encode())
        self.clientSocket.send(msg.encode())
        self.sendMessage(endmsg)
    
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