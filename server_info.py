# A file used to store information related to the information sent by the server on the PI:

# Information on the values of headers sent:
import socket
import sys

ACK_VALUE = bytes([1])
PAYLOAD = bytes([2])
TEXT = bytes([3])

#############################################################################

# Information on the padding of c structs that are sent raw by the PI server:

header_type_bytes = 1
header_pad_bytes = 7  # Not sure?
header_nbytes_info = 4 # Verify this?
header_end_pad_bytes = 4 # Another four pad bytes to word align the struct

header_struct = (header_type_bytes,
                 header_pad_bytes,
                 header_nbytes_info)

payload_data_bytes = 2
payload_padding_bytes = 6
payload_time_bytes = 8
payload_time_offset = 8
payload_bytes = 16

#############################################################################


def int_from_net_bytes(b):
    """
    Converts a bytearray received from the network to an integer type 2 or 4 bytes.
    :param b: A bytearray
    :return: A 2 or 4 byte int.
    """
    if len(b) == 4:
        i = int.from_bytes(b, byteorder=sys.byteorder)
        # TODO need to check if my computer and raspberry pi differ in endianness.
        # Really hacky if this is the fix.
        return i#socket.ntohl(i)
    if len(b) == 2:
        i = int.from_bytes(b, byteorder=sys.byteorder)
        return i#socket.ntohs(i)

    return None
