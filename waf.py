#!/usr/bin/python
#MIT License

import SocketServer
import select
import socket
import logging
import re

logging.basicConfig(level = logging.DEBUG)

DEST_HOST = "127.0.0.1"
DEST_PORT = 1024
LISTEN_PORT = 1025

class CheckFail(Exception):
    pass

#********** RULE ************
#dir: 0 if client -> server
#     1 if server -> client
def check_buf(dir, buf):
    if re.search(r"['`/*\-#]|OR|AND|WHERE", buf, re.I):
        raise CheckFail()

class ClientHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        logging.info("accept %s", self.client_address)

        ssock = self.request
        dsock = socket.create_connection((DEST_HOST, DEST_PORT))

        conversations = []

        try:
            while True:
                rlist, wlist, xlist = select.select([ssock, dsock], [], [])

                if ssock in rlist:
                    buf = ssock.recv(4096)
                    if len(buf) == 0:
                        break
                    conversations.append((0, buf))
                    check_buf(0, buf)
                    dsock.send(buf)

                if dsock in rlist:
                    buf = dsock.recv(4096)
                    if len(buf) == 0:
                        break
                    conversations.append((1, buf))
                    check_buf(1, buf)
                    ssock.send(buf)
        except CheckFail:
            logging.info("--------------------%s filtered--------------------",
                    self.client_address)
            for dir, buf in conversations:
                if dir == 0:
                    dirstr = "client->server"
                else:
                    dirstr = "server->client"
                logging.info("%s %s %s", self.client_address, dirstr, buf)
            logging.info("--------------------end--------------------")

        dsock.shutdown(socket.SHUT_WR)
        while len(dsock.recv(4096)) > 0:
            pass
        dsock.close()

class ForkingTCPServer(SocketServer.ForkingMixIn, SocketServer.TCPServer):
    pass

if __name__ == "__main__":
    ForkingTCPServer.allow_reuse_address = True
    server = ForkingTCPServer(("", LISTEN_PORT), ClientHandler)
    logging.debug("listening on port %d" % LISTEN_PORT)
    server.serve_forever()
