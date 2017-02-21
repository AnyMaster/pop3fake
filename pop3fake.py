#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pop3fake, Simple POP3 server with file-based message for test purpose

@author: AnyMaster
https://github.com/AnyMaster/pop3fake

Based on code from Daniel Miller,
http://code.activestate.com/recipes/534131
"""

import logging
import os
import socket
import uuid

EOL = "\r\n"  # end of line chars


class SocketExt(socket.SocketType):
    def __init__(self, conn):
        self.conn = conn

    def send_resp(self, data):
        logging.info("[*] Sending: %r", data[:80])
        self.conn.sendall(data + EOL)

    def recv_command(self):
        data = list()
        while True:
            chunk = self.conn.recv(4096)
            if not chunk:
                logging.info("[-] Connection closed")
                return
            if EOL in chunk:
                data += chunk[:chunk.index(EOL)]
                break
            data += chunk
        data = "".join(data)
        logging.info("[+] Received: %r", data)

        return data


class Message(object):
    def __init__(self, filename):
        with open(filename, "rb") as f_obj:
            self.data = f_obj.read()
            self.size = len(self.data)
            self.headers, self.body = self.data.split("\n\n", 1)
            self.body = self.body.split("\n")


def handle_user(*_):  # accept any
    return "+OK user accepted"


def handle_pass(*_):  # accept any
    return "+OK pass accepted"


def handle_stat(_, msg):
    return "+OK 1 {}".format(msg.size)


def handle_list(num, msg):
    if num is None:
        data = "+OK 1 messages ({0} octets){1}1 {0}{1}.".format(msg.size, EOL)
    elif num in "1":
        data = "+OK 1 {}".format(msg.size)
    else:
        data = "-ERR no such message, only 1 message in maildrop"

    return data


def handle_uidl(num, _):
    if num is None:
        data = "+OK {0}1 {1}{0}.".format(EOL, uuid.uuid4().hex)
    elif num in "1":
        data = "+OK 1 {}".format(uuid.uuid4().hex)
    else:
        data = "-ERR no such message"

    return data


def handle_capa(*_):
    data = ["+OK List of capabilities follows", EOL]
    data += [command + EOL for command in commands]
    data += "."

    return "".join(data)


def handle_top(params, msg):
    num, lines = params.split()
    if num in "1":
        data = ["+OK top of message follows", EOL]
        data += msg.headers, EOL, EOL
        data += EOL.join(msg.body[:int(lines)]), EOL, "."
        data = "".join(data)
    else:
        data = "-ERR no such message"

    return data


def handle_retr(num, msg):
    if num in "1":
        data = "+OK {0} octets{1}{2}{1}.".format(msg.size, EOL, msg.data)
    else:
        data = "-ERR no such message with number {}".format(num)

    return data


def handle_dele(num, _):
    if num in "1":
        data = "+OK message 1 deleted"
    else:
        data = "-ERR no such message with number {}".format(num)

    return data


def handle_noop(*_):
    return "+OK"


def handle_quit(*_):
    return "+OK pop3fake server signing off"


commands = {
    "USER": handle_user,
    "PASS": handle_pass,
    "STAT": handle_stat,
    "LIST": handle_list,
    "UIDL": handle_uidl,
    "TOP": handle_top,
    "RETR": handle_retr,
    "DELE": handle_dele,
    "NOOP": handle_noop,
    "CAPA": handle_capa,
    "QUIT": handle_quit}


def process_conn(conn, msg):
    conn.settimeout(5)
    conn = SocketExt(conn)
    conn.send_resp("+OK pop3fake server ready")

    while True:
        try:
            data = conn.recv_command()
            if not data:
                break

            data_split = data.split(None, 1)
            command = data_split[0]
            param = data_split[1] if len(data_split) > 1 else None

            if command in commands:
                conn.send_resp(commands[command](param, msg))
                if command in "QUIT":
                    break
            else:
                conn.send_resp("-ERR unknown command")

        except socket.timeout:
            logging.error("[-] Disconnect - client idle timeout")
            break
        except socket.error:
            logging.error("[-] Connection closed/lost")
            break

    conn.close()


def serve(filename, host="", port=110):
    """
    Serving message from file like POP3 server

    :param filename: name of message file
    :param host: if "" - bind to all IP, "localhost" - for local usage
    :param port: port bind to
    """

    msg = Message(filename)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))

    if not host:
        host = socket.gethostname()
    logging.info("[+] pop3fake serving '%s' on %s:%s", filename, host, port)

    try:
        while True:
            sock.listen(1)
            conn, address = sock.accept()
            logging.debug('[+] Connected by %s', address)
            process_conn(conn, msg)
    except (SystemExit, KeyboardInterrupt):
        logging.info("[+] pop3fake server stopped")

    try:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
    except socket.error:
        pass


if __name__ == "__main__":

    MSG_FILE = "message.txt"

    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    logging.info("[*] Starting POP3 server")

    if os.path.isfile(MSG_FILE):
        serve(MSG_FILE)
    else:
        logging.error("[-] File '{}' not found".format(MSG_FILE))
