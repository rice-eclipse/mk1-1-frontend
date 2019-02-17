"""
This file defines GUIBackend, which is responsible for getting
processing items from the network queue. The frontend communicates
with the backend using a Front2BackAdapter, which is defined in
in GUIController
"""

import csv
import struct
import time

from queue import Queue
from concurrency import run_async
from logger import LogLevel, Logger
from networking.networker import Networker, ServerInfo
from scipy import stats


class GUIBackend:
    """
    This class is responsible for getting data from the network queue
    and storing them in queues. It also has an instance of Networker
    for sending data back to the Pi.
    """

    def __init__(self, back2front_adapter, config):
        self.back2front_adapter = back2front_adapter
        self.config = config
        self.info = ServerInfo()

        self.nw_queue = Queue()

        self.logger = Logger(name='backend',
                             display_func=self.back2front_adapter.display_msg,
                             level=LogLevel.DEBUG,
                             outfile='backend.log',
                             display_log=False)

        nw_logger = Logger(name='networker',
                           display_func=self.back2front_adapter.display_msg,
                           level=LogLevel.DEBUG,
                           outfile='networker.log',
                           display_log=True)

        self.nw = Networker(nw_logger, self.config, queue=self.nw_queue)

        self.Q_LC1 = []
        self.Q_LC2 = []
        self.Q_LC3 = []
        self.Q_LC_MAIN = []

        self.Q_TC1 = []
        self.Q_TC2 = []
        self.Q_TC3 = []

        self.Q_FEED = []
        self.Q_INJE = []
        self.Q_COMB = []

        self.queues = [self.Q_LC1, self.Q_LC2, self.Q_LC3, self.Q_LC_MAIN, self.Q_TC1,
                       self.Q_TC2, self.Q_TC3, self.Q_FEED, self.Q_INJE, self.Q_COMB]

        for queue in self.queues:
            queue.append((0, 0))

        # A dictionary to match mtypes to queues (see _process_recv_message)
        self.queue_dict = {
            ServerInfo.LC1_SEND: self.Q_LC1,
            ServerInfo.LC2_SEND: self.Q_LC2,
            ServerInfo.LC3_SEND: self.Q_LC3,
            ServerInfo.LC_MAIN_SEND: self.Q_LC_MAIN,
            ServerInfo.TC1_SEND: self.Q_TC1,
            ServerInfo.TC2_SEND: self.Q_TC2,
            ServerInfo.TC3_SEND: self.Q_TC3,
            ServerInfo.PT_FEED_SEND: self.Q_FEED,
            ServerInfo.PT_COMB_SEND: self.Q_COMB,
            ServerInfo.PT_INJE_SEND: self.Q_INJE
        }

        self.calib_points = []

    def send_text(self, s):
        """
        Sends unicode text across the network.
        @param s: The string to send.
        """
        self.nw.send(str.encode(s))

    def send_num(self, i):
        """
        Sends a number across the network.
        @param i: The number to send.
        """
        self.nw.send(int.to_bytes(i, byteorder='big', length=4))

    def send(self, b):
        """
        Sends a byte across the network.
        @param b: The byte to send.
        """
        self.nw.send(b)

    def connect(self, address, port):
        """
        Connects to a given port at a given address.
        @param address: The address to connect to.
        @param port: The port.
        """
        self.nw.update_server_info(addr=address)
        self.nw.connect(addr=address, port=port)

    def disconnect(self):
        """
        Disconnects the current network connection.
        """
        self.nw.disconnect()

    def get_all_queues(self):
        """
        Returns all queues that are being used to store data.
        @return: A list of queues containing data.
        """
        return self.queues

    def get_queue(self, name):
        """
        Gets a particular queue by its name, e.g. "LC1"
        @param name: The name of the queue to return.
        @return: The queue corresponding to the given name.
        """
        return self.queue_dict[name]

    @run_async
    def start(self):
        """
        Starts the model by defining a coroutine that continuously
        processes items in the network queue.
        """
        while True:
            time.sleep(0.1)
            if not self.nw.connected:
                continue

            self._process_recv_message()

    def _process_recv_message(self):
        """
        Processes new messages from the network queue and checks that they
        are valid before placing data in the appropriate queue. In theory also
        processes other types of messages, but those cases aren't used right now.
        """
        if self.nw_queue.qsize() > 0:
            self.logger.debug("Processing Messages")

        while self.nw_queue.qsize() > 0:
            mtype, nbytes, message = self.nw_queue.get()
            self.logger.debug("Processing message: Type:" + str(mtype) + " Nbytes:" + str(nbytes))

            # If the data size isn't what we expect, do nothing
            if nbytes % self.nw.server_info.info.payload_bytes != 0:
                self.logger.error("Received PAYLOAD message with improper number of bytes:" + str(nbytes))
                return
            else:  # Check mtype to determine what to do
                if mtype == ServerInfo.ACK_VALUE:
                    pass
                elif mtype in ServerInfo.filenames.keys():
                    self.read_payload(message, nbytes, mtype)
                elif mtype == ServerInfo.TEXT:
                    print(message.decode('utf-8'))
                else:
                    self.logger.error("Received incorrect message header type" + str(mtype))

    def add_point(self, p):
        """
        Adds a point to the list of points to use
        when calculating a calibration cureve.
        @param p: A (raw_value, expected_value) ordered pair
        """
        self.calib_points.append(p)

    def get_calibration(self):
        """
        Uses the currently stored calibration points to
        calculate a calibration curve (slope and y-intercept).
        Assumes the curve is linear.
        @return: The slope and y-intercept for calibration
        """
        x, y = zip(*self.calib_points)

        return stats.linregress(x, y)[:2]

    def clear_calibration(self):
        """
        Removes any currently stored calibration points.
        """
        self.calib_points = []

    def read_payload(self, b, num_bytes, msg_type=None):
        """
        Reads a message corresponding to payload data, logging it to a log
        file and placing the data in the queue. Calibration happens here.
        @param b: The byte array containing the message.
        @param num_bytes: The number of bytes in the message.
        @param msg_type: The type of message, i.e. which payload.
        @return: None if the server info has not been initialized.
        """
        info = self.nw.server_info.info
        payload_bytes = info.payload_bytes

        if not payload_bytes:
            return None

        assert num_bytes % payload_bytes == 0

        if msg_type is not None and msg_type in ServerInfo.filenames.keys():
            save_file = open('logs/' + ServerInfo.filenames[msg_type] + '.log', 'a+')
            writer = csv.writer(save_file, delimiter=" ")
            # print("Starting logger for message")
        else:
            save_file = None
            writer = None

        bcount = 0
        while bcount < num_bytes:
            # d, t = self.payload_from_bytes(b[bcount: bcount + self.info.payload_bytes])
            d, t = struct.unpack("2Q", b[bcount: bcount + info.payload_bytes])

            bcount += info.payload_bytes

            if msg_type in ServerInfo.calibrations.keys():
                calibration = ServerInfo.calibrations[msg_type]
                cal = d * calibration[0] + calibration[1]
            else:
                cal = 0

            if not save_file:
                writer.writerow([str(t), str(d), str(cal)])
            if self.queue_dict[msg_type] is not None:
                self.queue_dict[msg_type].append((cal, t))
                # out_queue.put((cal, t))

        if save_file:
            save_file.close()
