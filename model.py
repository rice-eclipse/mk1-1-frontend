import time
from queue import Queue

from concurrency import run_async
from logger import LogLevel, Logger
from networking.networker import Networker, ServerInfo


class GUIBackend:
    def __init__(self, config):

        self.config = config

        self.nw_queue = Queue()
        self.nw = Networker(self.config, queue=self.nw_queue, loglevel=LogLevel.INFO)

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

        self.gui_logs = ["GUI Logs Ready"]
        self.logger = Logger(name='GUI', log_list=self.gui_logs, level=LogLevel.INFO, outfile='gui.log')

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
                    self.nw.server_info.read_payload(message, nbytes, self.queue_dict[mtype], mtype)
                elif mtype == ServerInfo.TEXT:
                    print(message.decode('utf-8'))
                    # sys.stdout.write(message.decode('utf-8'))
                else:
                    self.logger.error("Received incorrect message header type" + str(mtype))
