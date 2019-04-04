import json

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
    def getUrl(message):
        REQUEST_LINE = 0
        VALUE_INDEX = 1

        try:
            spaceIndex = message[REQUEST_LINE][VALUE_INDEX].find(" ")
            return message[REQUEST_LINE][VALUE_INDEX][ : spaceIndex]
        except:
            return ""

    @staticmethod
    def getResponseLine(message):
        line = ""
        ID = "HTTP"

        for character in message:
            if (chr(character) == '\r'):
                continue
            if (chr(character) == '\n'):
                break
            line += chr(character)

        if (line[ : len(ID)] == ID):
            return line
        else:
            return None

    @staticmethod
    def getResponseHeader(message):
        line = ""
        ID = "HTTP"
        isLastLine = False

        for character in message:
            if (chr(character) == '\r'):
                continue
            if (chr(character) == '\n'):
                if (isLastLine):
                    break
                line += "\n"
                isLastLine = True
                continue

            isLastLine = False
            line += chr(character)

        if (line[ : len(ID)] == ID):
            return line
        else:
            return None


    @staticmethod
    def getPragmaFlag(message):
        line = ""
        PRAGMA = "pragma: "
        CACHE_CONTROL = "Cache-Control: "

        for character in message:
            if (chr(character) == '\r'):
                continue
            if (chr(character) == '\n'):
                if (line[ : len(PRAGMA)] == PRAGMA):
                    return line[len(PRAGMA) : ]

                if (line[ : len(CACHE_CONTROL)] == CACHE_CONTROL):
                    
                    return line[len(CACHE_CONTROL) : ]
    
                line = ""
                continue
            line += chr(character)
        else:
            return ""

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

    @staticmethod
    def getExpiryDate(message):
        line = ""
        EXPIRY = "Expires: "
        EXPIRY_FORMAT = "Expires: XXX, "
        GMT = " GMT"

        for character in message:
            if (chr(character) == '\r'):
                continue
            if (chr(character) == '\n'):
                if (line[ : len(EXPIRY)] == EXPIRY):
                    return line[len(EXPIRY_FORMAT) : len(line) - len(GMT)]
                line = ""
                continue
            line += chr(character)
        else:
            return ""

    @staticmethod
    def getRequestMessage(httpMessage):
        message = ""
        for i, x in enumerate(httpMessage):
            if (i == 0):
                message += x[0] + " " + x[1] + "\r\n"                
            else:
                message += x[0] + ":" + x[1] + "\r\n"
        
        message += "\r\n"

        return message

    @staticmethod
    def getHostName(httpMessage):
        HOSTNAME_LINE = 1
        URL_INDEX = 1
        SPACE_INDEX = 0

        try:
            return httpMessage[HOSTNAME_LINE][URL_INDEX][SPACE_INDEX + 1 : ]
        except:
            return None

    @staticmethod
    def getString(data):
        string = ""

        for character in data:
            string += character
        
        return string

    @staticmethod
    def changeTheContentLength(messageString, length):
        line = ""
        LENGTH_KEY = "Content-Length: "

        if (LENGTH_KEY in messageString):
            lengthIndex = messageString.find(LENGTH_KEY) + len(LENGTH_KEY)
            newLineIndex = messageString[lengthIndex : ].find("\r\n")
            
            messageString = messageString[ : lengthIndex] +\
                    str(int(messageString[lengthIndex : lengthIndex + newLineIndex]) + length) +\
                    messageString[lengthIndex + newLineIndex : ]
            return messageString
        return ""

    @staticmethod
    def getBody(data, injectedMessage):
        BODY = "<body>"
        BR = "<br>"
        
        messageString = data.decode()
        
        if (BODY in messageString):
            messageString = Parser.changeTheContentLength(messageString,\
                    len(injectedMessage) + len(BR))
            bodyIndex = messageString.index(BODY) + len(BODY)
            messageString = messageString[ : bodyIndex] +\
                    injectedMessage + BR + messageString[bodyIndex : ]
        data = bytes(messageString, 'utf-8')

        return data

    @staticmethod
    def getHeaderValue(message, header):
        line = ""
        DELIMITER = ": "

        for character in message:
            try:
                if (chr(character) == '\r'):
                    continue
                if (chr(character) == '\n'):
                    if (len(line) > len(header) and line[ : len(header)] == header):
                        return line[len(header) + len(DELIMITER) : ]
                    line = ""
                    continue
                line += chr(character)
            except:
                pass
        else:
            return ""

    @staticmethod
    def getContent(completedData):
        isLastLine = False
        contentIndex = 0

        for character in completedData:
            contentIndex += 1

            if (chr(character) == '\r'):
                continue
            if (chr(character) == '\n'):
                if (isLastLine):
                    break
                isLastLine = True
                continue
            isLastLine = False
        
        if (len(completedData) > 0):
            return completedData[contentIndex : ], contentIndex
        return "", -1

    @staticmethod
    def getUnzippedContent(content):
        return content

    @staticmethod
    def getUnzippedData(completedData):
        content, contentIndex = Parser.getContent(completedData)
        newContent = Parser.getUnzippedContent(content)
        return completedData[ : contentIndex] + newContent 