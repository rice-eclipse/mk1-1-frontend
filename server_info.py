# A file used to store information related to the information sent by the server on the PI:

# Information on the values of headers sent:
import csv

class ServerInfo:
    """
    A class that contains all the configuration info, like if we're connected to a pi or not.
    Used to track manually unpacking structs and other dumb stuff.
    """
    def __init__(self):
        self.on_pi = True
        self.info = ServerInfo.PiInfo
        pass

    def int_from_net_bytes(self, b):
        """
        Converts a bytearray received from the network to an integer type 2 or 4 bytes.
        :param b: A bytearray
        :return: A 2 or 4 byte int.
        """
        if len(b) == 4:
            i = int.from_bytes(b, self.info.byteorder)
            # TODO need to check if my computer and raspberry pi differ in endianness.
            # Really hacky if this is the fix.
            # print("4 byte int:" + str(i))
            return i  # socket.ntohl(i)
        if len(b) == 2:
            i = int.from_bytes(b, self.info.byteorder)
            # print("2 byte int:" + str(i))
            return i  # socket.ntohs(i)

        if (len(b) == 8):
            i = int.from_bytes(b, self.info.byteorder)
            # NO 8 byte byteswap, which is an annoying problem.
            # Not sure if we need it at all however.
            # print("8 byte int:" + str(i))
            return i

        return None

    ACK_VALUE = bytes([1])
    PAYLOAD = bytes([2])
    TEXT = bytes([3])
    UNSET_VALVE = bytes([4])
    SET_VALVE = bytes([5])
    UNSET_IGNITION = bytes([6])
    SET_IGNITION = bytes([7])
    NORM_IGNITE = bytes([8])
    HALF_SEC_IGNITE = bytes([19])
    THREEQ_SEC_IGNITE = bytes([20])
    LC_MAIN_SEND = bytes([9])
    LC1_SEND = bytes([10])
    LC2_SEND = bytes([11])
    LC3_SEND = bytes([12])
    PT_FEED_SEND = bytes([13])
    PT_INJE_SEND = bytes([14])
    PT_COMB_SEND = bytes([15])
    TC1_SEND = bytes([16])
    TC2_SEND = bytes([17])
    TC3_SEND = bytes([18])

    filenames = {
        LC1_SEND: 'LC1',
        LC_MAIN_SEND: 'LC_MAIN',
        LC2_SEND: 'LC2',
        LC3_SEND: 'LC3',
        PT_FEED_SEND: 'PT_FEED',
        PT_COMB_SEND: 'PT_COMB',
        PT_INJE_SEND: 'PT_INJE',
        TC1_SEND: 'TC1',
        TC2_SEND: 'TC2',
        TC3_SEND: 'TC3'
    }

    calibrations = {
        LC1_SEND: (1, 0),
        LC_MAIN_SEND: (0.1365, -66.885),
        LC2_SEND: (1, 0),
        LC3_SEND: (1, 0),
        PT_FEED_SEND: (-0.275787487, 1069),
        PT_COMB_SEND: (-0.2810327855, 1068),
        PT_INJE_SEND: (-0.2782331275, 1045),
        TC1_SEND: (0.1611, -250),
        TC2_SEND: (0.1611, -250),
        TC3_SEND: (0.1611, -250)
    }

    class PiInfo:
        byteorder='little'

        header_type_bytes = 1
        header_nbytes_offset = 4
        header_nbytes_info = 4
        header_end_pad_bytes = 0
        header_size = 8

        payload_data_bytes = 2
        payload_padding_bytes = 6
        payload_time_bytes = 8
        payload_time_offset = 8
        payload_bytes = 16

    class OtherInfo:
        byteorder='little'

        header_type_bytes = 1
        header_nbytes_offset = 8
        header_nbytes_info = 4
        header_end_pad_bytes = 4
        header_size = 16

        payload_data_bytes = 2
        payload_padding_bytes = 6
        payload_time_bytes = 8
        payload_time_offset = 8
        payload_bytes = 16

    def payload_from_bytes(self, b):
        assert len(b) == self.info.payload_bytes

        data = b[:self.info.payload_data_bytes]
        data = self.int_from_net_bytes(data)

        t = b[self.info.payload_time_offset:self.info.payload_time_offset + self.info.payload_time_bytes]
        t = self.int_from_net_bytes(t)

        return data, t

    def read_payload(self, b, nbytes, out_queue, mtype=None):
        assert nbytes % self.info.payload_bytes == 0

        #print(mtype, mtype in ServerInfo.filenames.keys())
        #print(ServerInfo.filenames.keys())

        if (mtype != None and mtype in ServerInfo.filenames.keys()):
            save_file = open('logs/' + ServerInfo.filenames[mtype] + '.log', 'a+')
            writer = csv.writer(save_file, delimiter=" ")
            #print("Starting logger for message")
        else:
            save_file = None
            writer = None

        bcount = 0
        while bcount < nbytes:
            d, t = self.payload_from_bytes(b[bcount: bcount + self.info.payload_bytes])
            bcount += self.info.payload_bytes
            # TODO handle multiple out queues

            #if (mtype in ServerInfo.averages.keys()):
            #    ServerInfo.averages[mtype] = 0.5 * ServerInfo.averages[mtype] + 0.5 * d

            if (mtype in ServerInfo.calibrations.keys()):
                calib = ServerInfo.calibrations[mtype]
                cal = d * calib[0] + calib[1]
            else:
                cal = 0

            if (save_file != None):
                writer.writerow([str(t), str(d), str(cal)])
            if (out_queue is not None):
                out_queue.append((cal, t))
                # out_queue.put((cal, t))

        if (save_file is not None):
            save_file.close()

    def decode_header(self, b):
        htype = b[:self.info.header_type_bytes]

        #print(htype)
        nbytesb = b[self.info.header_nbytes_offset: self.info.header_nbytes_offset + self.info.header_nbytes_info]

        return htype, self.int_from_net_bytes(nbytesb)
