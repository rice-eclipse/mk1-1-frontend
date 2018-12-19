import socket
import threading

from queue import Queue

# A class used to handle all the networking:
import sys

import time

from logger import LogLevel, Logger
from networking.server_info import*
from config import config

# MAJOR TODO move this networker to processing requests on its own thread and then let it attempt reconnection.


class Networker:
    class NWThread(threading.Thread):
        def __init__(self, threadID, name, counter, nw):

            assert(isinstance(nw, Networker))

            threading.Thread.__init__(self)
            self.threadID = threadID
            self.name = name
            self.counter = counter
            self.nw = nw

        def run(self):
            while True:
                # Ensure we are connected:
                self.nw.conn_event.wait()

                # Try to receive a message:
                t, nb, m = self.nw.read_message()
                # print(t)
                if (t is not None):
                    self.nw.out_queue.put((t, nb, m))

    @staticmethod
    def make_socket():
        tcp_sock = socket.socket()
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 50ms timeout, with the intent of giving just a bit of time if receiving.
        tcp_sock.settimeout(5)
        udp_sock.settimeout(5)

        return tcp_sock, udp_sock

    def __init__(self, queue=None, loglevel=LogLevel.DEBUG):
        self.tcp_sock, self.udp_sock = self.make_socket()
        self.recv_sock = None
        self.addr = None
        self.port = None
        self.connected = False
        self.trying_connect = False
        # TODO for now we only have the data receiving on a separate thread because that was straightforward:
        self.out_queue = queue if queue is not None else Queue()
        self.conn_event = threading.Event()

        self.thr = Networker.NWThread(1, 'NWThread', 1, self)
        self.thr.start()

        self.network_logs = ["Network Logs Ready"]
        self.logger = Logger(name='networker', log_list=self.network_logs, level=loglevel, outfile='networker.log')

        self.server_info = ServerInfo()

        self.logger.info("Initialized")

    def update_server_info(self, addr):
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
                if (config.get("Server", "Protocol") == "UDP"):
                    self.udp_sock.bind(('', int(self.port)))
                    self.recv_sock = self.udp_sock
                    self.logger.error("Receiving on UDP")
                else:
                    self.recv_sock = self.tcp_sock
                    self.logger.error("Receiving on TCP")
            except socket.timeout:
                self.logger.error("Connect timed out.")
                sys.exit(0)
            except OSError as e:
                self.logger.error("Connection failed. OSError:" + e.strerror)
                self.trying_connect = False
            except:
                self.logger.error("Connect: Unexpected error:" + str(sys.exc_info()[0]))
                self.trying_connect = False
            else:
                self.update_server_info(self.addr)
                self.logger.error("Successfully connected. Using info " + self.server_info.info.__name__)
                self.trying_connect = False
                self.connected = True
                # TODO make this variable not some hacky global.
                self.conn_event.set()

    def disconnect(self):
        """
        Disconnects and resets and connection information.
        :return: None
        """
        if not self.connected:
            return

        self.conn_event.clear()
        self.connected = False
        self.logger.warn("Socket disconnecting:")
        self.tcp_sock.close()
        self.udp_sock.close()
        self.recv_sock = None

        # Recreate the socket so that we aren't screwed.
        self.tcp_sock, self.udp_sock = self.make_socket()

    def send(self, message):
        """
        Sends a bytearray.
        :param message:
        :return: True if no exceptions were thrown:
        """
        # TODO logging levels?
        self.logger.debug("Sending message:")
        # TODO proper error handling?
        try:
            self.tcp_sock.send(message)
        except socket.timeout:
            self.logger.error("Socket timed out while sending")
            self.disconnect()
        except OSError as e:
            self.logger.error("Connection failed. OSError:" + e.strerror)
            self.disconnect()
        except:
            self.logger.error("Unexpected error:" + str(sys.exc_info()[0]))
            self.disconnect()
        else:
            self.logger.info("Message sent")
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
            message = self._recv(nbytes)

        if (message is not None):
            if (nbytes <= 64):
                self.logger.debug("Received Full Message: Type:" + str(htype) +
                           " Nbytes:" + str(nbytes) + " message" + str(message))
            else:
                self.logger.debug("Received Full Message: Type:" + str(htype) +
                                  " Nbytes:" + str(nbytes))

        time.sleep(0.01)

        return htype, nbytes, message

    def read_header(self):
        """
        Reads a data header from PI server.
        :return: The header type, The number of bytes
        """
        b = self._recv(self.server_info.info.header_size)
        if (len(b) == 0):
            return None, None

        htype, nbytes = struct.unpack(self.server_info.info.header_format_string, b)

        self.logger.debugv("Received message header: Type:" + str(htype) + " Nbytes:" + str(nbytes))

        return htype, nbytes

    def _recv(self, nbytes):
        """
        Receives a message of length nbytes from the socket. Will retry until all bytes have been received.
        :param nbytes: The number of bytes to receive.
        :return: The bytes.
        """
        #print("Attempting to read " + str(nbytes) + " bytes")
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
        except:
            self.logger.error("Read: Unexpected error:" + str(sys.exc_info()[0]))
            self.disconnect()
        else:
            return outb

        return bytes([])
