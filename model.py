import csv
import struct
import time
from queue import Queue

from concurrency import run_async
from logger import LogLevel, Logger
from networking.networker import Networker, ServerInfo


class GUIBackend:
    def __init__(self, back2front_adapter, config):
        self.back2front_adapter = back2front_adapter
        self.config = config
        self.info = ServerInfo()

        self.nw_queue = Queue()

        backend_logs = ["Backend Logs Ready"]
        network_logs = ["Network Logs Ready"]

        self.logger = Logger(name='backend',
                             display_func=self.back2front_adapter.display_msg,
                             log_list=backend_logs,
                             level=LogLevel.DEBUG,
                             outfile='backend.log')

        nw_logger = Logger(name='networker',
                           display_func=self.back2front_adapter.display_msg,
                           log_list=network_logs,
                           level=LogLevel.DEBUG,
                           outfile='networker.log')

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


    def send_text(self, s):
        self.nw.send(str.encode(s))

    def send_num(self, i):
        self.nw.send(int.to_bytes(i, byteorder='big', length=4))

    def send_byte(self, b):
        self.nw.send(bytes([b]))

    def send(self, b):
        self.nw.send(b)

    def connect(self, address, port):
        self.nw.update_server_info(addr=address)
        self.nw.connect(addr=address, port=port)

    def ignite(self):
        # todo send some numbers over
        self.logger.error("IGNITING!!!")
        self.nw.send(ServerInfo.NORM_IGNITE)

    def disconnect(self):
        self.nw.disconnect()

    def get_all_queues(self):
        return self.queues

    def get_queue(self, name):
        return self.queue_dict[name]

    @run_async
    def start(self):
        while True:
            time.sleep(0.1)
            if not self.nw.connected:
                continue

            self._process_recv_message()

    def _process_recv_message(self):
        """
        Processes new messages from nw_queue and give them to the appropriate GUI thread.
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
                    self.read_payload(message, nbytes, self.queue_dict[mtype], mtype)
                elif mtype == ServerInfo.TEXT:
                    print(message.decode('utf-8'))
                else:
                    self.logger.error("Received incorrect message header type" + str(mtype))

    def read_payload(self, b, nbytes, out_queue, mtype=None):
        info = self.nw.server_info.info

        if not info:
            return

        assert nbytes % info == 0

        if mtype != None and mtype in ServerInfo.filenames.keys():
            save_file = open('logs/' + ServerInfo.filenames[mtype] + '.log', 'a+')
            writer = csv.writer(save_file, delimiter=" ")
            # print("Starting logger for message")
        else:
            save_file = None
            writer = None

        bcount = 0
        while bcount < nbytes:
            # d, t = self.payload_from_bytes(b[bcount: bcount + self.info.payload_bytes])
            d, t = struct.unpack("2Q", b[bcount: bcount + info.payload_bytes])

            bcount += info.payload_bytes

            if mtype in ServerInfo.calibrations.keys():
                calibration = ServerInfo.calibrations[mtype]
                cal = d * calibration[0] + calibration[1]
            else:
                cal = 0

            if not save_file:
                writer.writerow([str(t), str(d), str(cal)])
            if out_queue is not None:
                out_queue.append((cal, t))
                # out_queue.put((cal, t))

        if save_file:
            save_file.close()
