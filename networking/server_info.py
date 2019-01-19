# A file used to store information related to the information sent by the server on the PI:

# Information on the values of headers sent:
import csv
import struct

class ServerInfo:
    """
    A class that contains all the configuration info, like if we're connected to a pi or not.
    Used to track manually unpacking structs and other dumb stuff.
    """

    def __init__(self):
        self.on_pi = True
        self.info = ServerInfo.PiInfo
        pass

    ACK_VALUE = bytes([1])
    PAYLOAD = bytes([2])
    TEXT = bytes([3])
    UNSET_VALVE = bytes([4])
    SET_VALVE = bytes([5])
    UNSET_IGNITION = bytes([6])
    SET_IGNITION = bytes([7])
    NORM_IGNITE = bytes([8])
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
    SET_WATER = bytes([19])
    UNSET_WATER = bytes([20])
    SET_GITVC = bytes([21])
    UNSET_GITVC = bytes([22])

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
        LC_MAIN_SEND: (-.03159, 105),
        LC1_SEND: (.0093895, 0),
        LC2_SEND: (-.0092222, 0),
        LC3_SEND: (.0097715, 0),
        PT_FEED_SEND: (-0.275787487, 1069),
        PT_COMB_SEND: (-0.2810327855, 1068),
        PT_INJE_SEND: (-0.2782331275, 1045),
        TC1_SEND: (0.1611, -250),
        TC2_SEND: (0.1611, -250),
        TC3_SEND: (0.1611, -250)
    }

    class PiInfo:
        byteorder = 'little'

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

        header_format_string = "c3xi"

    class OtherInfo:
        byteorder = 'little'

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

        header_format_string = "c7xi4x"
