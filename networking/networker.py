"""
This file defines Networker and NWThread, which handle networking
for mission control. It is used by GUIBackend defined in model.py.
"""

import socket
import struct

from queue import Queue

import sys

from select import select

from concurrency import run_async
from networking.server_info import*


class Networker:
    """
    The networker class abstracts network processes such as
    connect, disconnect, send, and receive for the sockets
    we are using.
    """

    @run_async
    def run(self):
        """
        Start interacting with the network on a new thread.
        """
        while self.connected and self.in_fds or self.out_fds:
            # print(self.nw.in_fds, self.nw.out_fds)
            _input, _output, _except = select(self.in_fds, self.out_fds, [])

            # This happens if we disconnect. This thread will end
            # and a new one will be started.
            if -1 in _input or -1 in _output:
                return

            t, nb, m = self.read_message()
            if t is not None:
                self.out_queue.put((t, nb, m))

            while not self.send_queue.empty():
                send_item = self.send_queue.get()
                self.send(send_item)

    def make_socket(self):
        """
        Creates a tcp and udp socket if they do not already
        exist. These sockets are created but may not actually
        be used. See connect() for how they are used. Also,
        remember to set these sockets to None after you
        close them so you can re-create them here.
        """
        if self.tcp_sock is None:
            self.tcp_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            self.tcp_sock.settimeout(5)

        if self.udp_sock is None:
            self.udp_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self.udp_sock.settimeout(5)

    def __init__(self, logger, config, queue):
        self.logger = logger
        self.config = config
        self.tcp_sock = None
        self.udp_sock = None
        self.recv_sock = None
        self.addr = None
        self.port = None
        self.connected = False
        self.trying_connect = False
        self.out_queue = queue
        self.send_queue = Queue()

        self.in_fds = []
        self.out_fds = []

        self.server_info = ServerInfo()

        # self.logger.info("Initialized")

    def update_server_info(self, addr):
        """
        Updates the server info information to be compatible
        with either the Pi or the local machine.
        @param addr: The address we are connected to.
        """
        host = socket.gethostbyaddr(addr)[0]
        if host != 'raspberry' and host != 'Pi01':
            self.server_info.info = ServerInfo.OtherInfo
        else:
            self.server_info.info = ServerInfo.PiInfo

    def connect(self, addr=None, port=None):
        """
        Connects to a given address and port or just tries to
        reconnect (if args are none or same).
        @param addr: The address to connect to.
        @param port: The port to connect to.
        @return: None
        """
        # If the port or address have changed we should disconnect.
        if addr is not None and self.addr != addr:
            self.disconnect()
            self.addr = addr

        if port is not None and self.port != port:
            self.disconnect()
            self.port = port

        if self.connected:
            return

        self.trying_connect = True
        self.make_socket()
        while self.trying_connect:
            # noinspection PyBroadException
            try:
                self.tcp_sock.connect((self.addr, int(self.port)))
                self.out_fds = [self.tcp_sock]
                self.logger.error("Transmitting on TCP")
                if self.config.get("Server", "Protocol") == "UDP":
                    self.udp_sock.bind(('0.0.0.0', int(self.port)))
                    self.recv_sock = self.udp_sock
                    self.logger.error("Receiving on UDP")
                else:
                    self.recv_sock = self.tcp_sock
                    self.logger.error("Receiving on TCP")
                    # TODO this doesn't work
                self.in_fds = [self.recv_sock]
            except socket.timeout:
                self.logger.error("Connect timed out.")
                sys.exit(0)
            except OSError as e:
                self.logger.error("Connection failed. OSError:" + e.strerror)
                self.trying_connect = False
            except RuntimeError as e:
                self.logger.error("Connection failed. RuntimeError: " + str(e))
                self.trying_connect = False
            except BaseException:
                self.logger.error("Connect: Unexpected error:" + str(sys.exc_info()[0]))
                self.trying_connect = False
            else:
                self.update_server_info(self.addr)
                self.logger.error("Successfully connected. Using info " + self.server_info.info.__name__)
                self.trying_connect = False
                self.connected = True
                self.run()
                # TODO make this variable not some hacky global.

    def disconnect(self):
        """
        Disconnects and resets the connection information
        and sockets being used.
        @return: None
        """
        if not self.connected:
            return

        self.connected = False
        self.logger.warn("Socket disconnecting")
        self.tcp_sock.close()
        self.udp_sock.close()
        self.tcp_sock = None
        self.udp_sock = None
        self.in_fds.clear()
        self.out_fds.clear()

        # Create new lists just in in case data races happen
        self.in_fds = []
        self.out_fds = []

    def send(self, message):
        """
        Sends a bytearray.
        @param message:
        @return: True if no exceptions were thrown:
        """
        # TODO logging levels?
        self.logger.info("Sending message: " + str(message))
        # TODO proper error handling?
        # noinspection PyBroadException
        try:
            self.tcp_sock.send(message)
        except socket.timeout:
            self.logger.error("Socket timed out while sending")
            self.disconnect()
        except OSError as e:
            self.logger.error("Connection failed. OSError:" + e.strerror)
            self.disconnect()
        except BaseException:
            self.logger.error("Unexpected error:" + str(sys.exc_info()[0]))
            self.disconnect()
        else:
            return True

        return False

    def read_message(self):
        """
        Reads a full message including header from the PI server.
        @return: The header type, the number of bytes, the message.
        """
        if not self.connected:
            self.logger.error("Trying to read while not connected")
            raise Exception("Not connected. Cannot read.")

        # Assume the datagram is smaller than 4096 bytes
        result = self.recv_sock.recv(4096)

        header_size = self.server_info.info.header_size

        header = result[:header_size]
        payload = result[header_size:]
        htype, nbytes = struct.unpack(self.server_info.info.header_format_string, header)
        print(nbytes, len(payload))
        # TODO header size included in nbytes?
        return htype, nbytes - header_size, payload

        # if (message is not None):
        #     if (nbytes <= 64):
        #         self.logger.debug("Received Full Message: Type:" + str(htype) +
        #                    " Nbytes:" + str(nbytes) + " message" + str(message))
        #     else:
        #         self.logger.debug("Received Full Message: Type:" + str(htype) +
        #                           " Nbytes:" + str(nbytes))

        # time.sleep(0.01)
