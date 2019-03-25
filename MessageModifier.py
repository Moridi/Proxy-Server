class MessageModifier(object):
    
    def getProxyConnectionIndex(self, httpMessage):
        PROXY_CONNECTION = "Proxy-Connection"
        FIELD_PART = 0

        index = [i for i, x in enumerate(httpMessage) if(x[FIELD_PART] == PROXY_CONNECTION)]
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
        index = self.getProxyConnectionIndex(httpMessage)
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
