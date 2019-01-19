import socket
import struct
import threading

from queue import Queue

import sys

import time
from select import select

from networking.server_info import*

# MAJOR TODO move this networker to processing requests on its own thread and then let it attempt reconnection.


class Networker:
    class NWThread(threading.Thread):
        def __init__(self, thread_id, name, counter, nw):

            assert(isinstance(nw, Networker))

            threading.Thread.__init__(self)
            self.threadID = thread_id
            self.name = name
            self.counter = counter
            self.nw = nw

        def run(self):
            while self.nw.in_fds or self.nw.out_fds:
                # print(self.nw.in_fds, self.nw.out_fds)
                _input, _output, _except = select(self.nw.in_fds, self.nw.out_fds, [])

                for _ in _input:
                    t, nb, m = self.nw.read_message()
                    if t is not None:
                        self.nw.out_queue.put((t, nb, m))

                while not self.nw.send_queue.empty():
                    send_item = self.nw.send_queue.get()
                    self.nw.send(send_item)

    def make_socket(self):
        if not self.tcp_sock:
            self.tcp_sock = socket.socket(type=socket.SOCK_STREAM)
            self.tcp_sock.settimeout(50)

        if not self.udp_sock:
            self.udp_sock = socket.socket(type=socket.SOCK_DGRAM)
            self.udp_sock.settimeout(50)

    def __init__(self, logger, config, queue):
        self.logger = logger
        self.config = config
        self.tcp_sock = None
        self.udp_sock = None
        self.make_socket()
        self.recv_sock = None
        self.addr = None
        self.port = None
        self.connected = False
        self.trying_connect = False
        # TODO for now we only have the data receiving on a separate thread because that was straightforward:
        self.out_queue = queue
        self.send_queue = Queue()

        self.thr = Networker.NWThread(1, 'NWThread', 1, self)
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
        Connects to a given address and port or just tries to reconnect (if args are none or same).
        :param addr: The address to connect
        :param port: The port to connect to.
        :return: None
        """
        # First check if the port or address have changed and if so we should disconnect.
        if addr is not None and self.addr != addr:
            self.disconnect()
            self.addr = addr

        if port is not None and self.port != port:
            self.disconnect()
            self.port = port

        if self.connected:
            return

        self.trying_connect = True
        while self.trying_connect:
            try:
                self.tcp_sock.connect((self.addr, int(self.port)))
                self.out_fds = [self.tcp_sock]
                self.logger.error("Transmitting on TCP")
                if self.config.get("Server", "Protocol") == "UDP":
                    self.udp_sock.bind((self.addr, int(self.port)))
                    self.recv_sock = self.udp_sock
                    self.logger.error("Receiving on UDP")
                else:
                    self.recv_sock = self.tcp_sock
                    self.logger.error("Receiving on TCP")
                    # TODO this doesn't work
                self.in_fds = [self.recv_sock]
                self.thr.start()
            except socket.timeout:
                self.logger.error("Connect timed out.")
                sys.exit(0)
            except OSError as e:
                self.logger.error("Connection failed. OSError:" + e.strerror)
                self.trying_connect = False
            except BaseException:
                self.logger.error("Connect: Unexpected error:" + str(sys.exc_info()[0]))
                self.trying_connect = False
            else:
                self.update_server_info(self.addr)
                self.logger.error("Successfully connected. Using info " + self.server_info.info.__name__)
                self.trying_connect = False
                self.connected = True
                # TODO make this variable not some hacky global.

    def disconnect(self):
        """
        Disconnects and resets the connection information.
        :return: None
        """
        if not self.connected:
            return

        self.connected = False
        self.logger.warn("Socket disconnecting:")
        self.tcp_sock.close()
        self.udp_sock.close()
        self.recv_sock = None
        self.in_fds = []
        self.out_fds = []

        # Recreate the socket so that we aren't screwed.
        self.make_socket()

    def send(self, message):
        """
        Sends a bytearray.
        :param message:
        :return: True if no exceptions were thrown:
        """
        # TODO logging levels?
        self.logger.info("Sending message: " + str(message))
        # TODO proper error handling?
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
        :return: The header type, the number of bytes, the message.
        """
        if not self.connected:
            self.logger.error("Trying to read while not connected")
            raise Exception("Not connected. Cannot read.")

        htype, nbytes = self.read_header()
        # print(htype)

        if nbytes is None or nbytes == 0:
            message = None
        else:
            # message = self._recv(nbytes)
            # TODO
            message = self._recv(16)
            print(struct.unpack("2Q", message))

        # if (message is not None):
        #     if (nbytes <= 64):
        #         self.logger.debug("Received Full Message: Type:" + str(htype) +
        #                    " Nbytes:" + str(nbytes) + " message" + str(message))
        #     else:
        #         self.logger.debug("Received Full Message: Type:" + str(htype) +
        #                           " Nbytes:" + str(nbytes))

        time.sleep(0.01)

        return htype, nbytes, message

    def read_header(self):
        """
        Reads a data header from PI server.
        :return: The header type, The number of bytes
        """
        b = self._recv(self.server_info.info.header_size)
        if len(b) == 0:
            return None, None

        htype, nbytes = struct.unpack(self.server_info.info.header_format_string, b)

        print("header", htype, nbytes)
        self.logger.debugv("Received message header: Type:" + str(htype) + " Nbytes:" + str(nbytes))

        return htype, nbytes

    def _recv(self, nbytes):
        """
        Receives a message of length nbytes from the socket.
        Will retry until all bytes have been received.
        :param nbytes: The number of bytes to receive.
        :return: The bytes.
        """
        # print("Attempting to read " + str(nbytes) + " bytes")
        outb = bytes([])
        bcount = 0
        try:
            while nbytes > 0:
                b = self.recv_sock.recv(nbytes)
                nbytes -= len(b)
                bcount += len(b)
                outb += b
        except socket.timeout:
            if bcount > 0:
                # TODO fix this.
                self.logger.error("Socket timed out during partial read. Major problem.")

            self.logger.error("Socket timed out. Trying to disconnect")
            self.disconnect()

        except OSError as e:
            self.logger.error("Read failed. OSError:" + e.strerror)
            self.disconnect()
        except BaseException:
            self.logger.error("Read: Unexpected error:" + str(sys.exc_info()[0]))
            self.disconnect()
        else:
            print(outb)
            return outb

        return bytes([])
