"""
A file used to store information about the
information sent by the server on the PI
"""


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
    SET_PVALVE = bytes([19])
    UNSET_PVALVE = bytes([20])
    SET_GITVC = bytes([21])
    UNSET_GITVC = bytes([22])
    LEAK_CHECK = bytes([23])
    FILL = bytes([24])
    FILL_IDLE = bytes([25])
    DEFAULT = bytes([26])

    @staticmethod
    def str2msg(s):
        """
        Maps a string (e.g. 'LC1_SEND') to the corresponding message above.
        Returns None if the string is not a valid message type. Useful when
        reading from config files.
        """
        if s == 'ACK_VALUE' or s == 'ack_value':
            return ServerInfo.ACK_VALUE
        elif s == 'PAYLOAD' or s == 'payload':
            return ServerInfo.PAYLOAD
        elif s == 'TEXT' or s == 'text':
            return ServerInfo.TEXT
        elif s == 'UNSET_VALVE' or s == 'unset_valve':
            return ServerInfo.UNSET_VALVE
        elif s == 'SET_VALVE' or s == 'set_valve':
            return ServerInfo.SET_VALVE
        elif s == 'UNSET_IGNITION' or s == 'unset_ignition':
            return ServerInfo.UNSET_IGNITION
        elif s == 'SET_IGNITION' or s == 'set_ignition':
            return ServerInfo.SET_IGNITION
        elif s == 'NORM_IGNITE' or s == 'norm_ignite':
            return ServerInfo.NORM_IGNITE
        elif s == 'LC_MAIN_SEND' or s == 'lc_main_send':
            return ServerInfo.LC_MAIN_SEND
        elif s == 'LC1_SEND' or s == 'lc1_send':
            return ServerInfo.LC1_SEND
        elif s == 'LC2_SEND' or s == 'lc2_send':
            return ServerInfo.LC2_SEND
        elif s == 'LC3_SEND' or s == 'lc3_send':
            return ServerInfo.LC3_SEND
        elif s == 'PT_FEED_SEND' or s == 'pt_feed_send':
            return ServerInfo.PT_FEED_SEND
        elif s == 'PT_INJE_SEND' or s == 'pt_inje_send':
            return ServerInfo.PT_INJE_SEND
        elif s == 'PT_COMB_SEND' or s == 'pt_comb_send':
            return ServerInfo.PT_COMB_SEND
        elif s == 'TC1_SEND' or s == 'tc1_send':
            return ServerInfo.TC1_SEND
        elif s == 'TC2_SEND' or s == 'tc2_send':
            return ServerInfo.TC2_SEND
        elif s == 'TC3_SEND' or s == 'tc3_send':
            return ServerInfo.TC3_SEND
        elif s == 'SET_PVALVE' or s == 'set_pvalve':
            return ServerInfo.SET_PVALVE
        elif s == 'UNSET_PVALVE' or s == 'unset_pvalve':
            return ServerInfo.UNSET_PVALVE
        elif s == 'SET_GITVC' or s == 'set_gitvc':
            return ServerInfo.SET_GITVC
        elif s == 'UNSET_GITVC' or s == 'unset_gitvc':
            return ServerInfo.UNSET_GITVC
        elif s == 'LEAK_CHECK' or s == 'leak_check':
            return ServerInfo.LEAK_CHECK
        elif s == 'FILL' or s == 'fill':
            return ServerInfo.FILL
        elif s == 'FILL_IDLE' or s == 'fill_idle':
            return ServerInfo.FILL_IDLE
        elif s == 'DEFAULT' or s == 'default':
            return ServerInfo.DEFAULT
        else:
            return None

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

    ### OLD LUNA CALIBRATION DATA, MOVED TO luna_config.ini ###
    # calibrations = {
    #     LC_MAIN_SEND: (-.03159, 105),
    #     LC1_SEND: (.0093895, 0),
    #     LC2_SEND: (-.0092222, 0),
    #     LC3_SEND: (.0097715, 0),
    #     PT_FEED_SEND: (-0.275787487, 1069),
    #     PT_COMB_SEND: (-0.2810327855, 1068),
    #     PT_INJE_SEND: (-0.2782331275, 1045),
    #     TC1_SEND: (0.1611, -250),
    #     TC2_SEND: (0.1611, -250),
    #     TC3_SEND: (0.1611, -250)
    # }

    class PiInfo:
        """
        The class that defines struct byte formats for the
        Pi.
        """
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
        """
        The class that defines struct byte formats for a
        server other than the Pi. This is usually localhost
        used for basic tests.
        """
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
