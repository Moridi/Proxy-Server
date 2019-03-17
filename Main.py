from ProxyServer import ProxyServer

if (__name__ == "__main__"):
    proxyServer = ProxyServer("config.json")
    proxyServer.run()