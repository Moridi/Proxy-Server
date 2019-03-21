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
