from Parser import Parser

DAYNAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

class MessageModifier(object):
    def __init__(self, userAgent, enable):
        self.userAgent = userAgent
        self.enable = enable

    def getLineIndex(self, httpMessage, field):
        FIELD_PART = 0

        index = [i for i, x in enumerate(httpMessage) if(x[FIELD_PART] == field)]
        if (len(index) == 0):
            return -1
        return index[0]

    def changeUrl(self, httpMessage):
        REQUEST_LINE = 0
        HOST_NAME_LINE = 1
        FIRST_PART = 0
        URL_PART = 1
        HTTP_PART = "http:/"

        try:
            spaceIndex = httpMessage[REQUEST_LINE][URL_PART].find(" ")
            httpMessage[REQUEST_LINE] = (httpMessage[REQUEST_LINE][FIRST_PART],\
                    httpMessage[REQUEST_LINE][URL_PART][len(HTTP_PART) +\
                    len(httpMessage[HOST_NAME_LINE][URL_PART]) : ])
        except:
            pass

    def removeProxyHeader(self, httpMessage):
        index = self.getLineIndex(httpMessage, "Proxy-Connection")
        try:
            httpMessage.pop(index)
        except:
            pass

    def changeHttpVersion(self, httpMessage):
        REQUEST_LINE = 0
        FIRST_PART = 0
        HTTP_VERSION_PART = 1
        HTTP_VERSION = "HTTP/1.0"

        try:
            httpVersionIndex = httpMessage[REQUEST_LINE][HTTP_VERSION_PART].find(" ") + 1
            httpMessage[REQUEST_LINE] = (\
                    httpMessage[REQUEST_LINE][FIRST_PART],\
                    httpMessage[REQUEST_LINE][HTTP_VERSION_PART][ : httpVersionIndex] +\
                    HTTP_VERSION + httpMessage[REQUEST_LINE][HTTP_VERSION_PART][\
                    httpVersionIndex + len(HTTP_VERSION) : ])
        except:
            pass

    def changeUserAgent(self, httpMessage):
        if (self.enable):
            FIRST_PART = 0

            userAgentIndex = self.getLineIndex(httpMessage, "User-Agent")
            try:
                httpMessage[userAgentIndex] = (
                        httpMessage[userAgentIndex][FIRST_PART], self.userAgent)            
            except:
                pass

    def injectHttpResponse(self, httpMessage):
        body = Parser.getBody(httpMessage)

    def changeIfModifiedSinceHeader(self, date, httpMessage):
        IF_MODIFIED_SINCE = "If-Modified-Since"
        HEADER_INDEX = 0
        VALUE_INDEX = 0

        formatedDate = DAYNAMES[date.weekday()] + ", " + str(date.day) + " " +\
                str(date.month) + " " + str(date.year) + " " + str(date.hour) + ":" +\
                str(date.minute) + ":" + str(date.second) + " GMT"
        
        for headerLine in httpMessage:
            if (headerLine[HEADER_INDEX] == IF_MODIFIED_SINCE):
                headerLine[VALUE_INDEX] = formatedDate
                break
        else:
            httpMessage.append((IF_MODIFIED_SINCE, formatedDate))