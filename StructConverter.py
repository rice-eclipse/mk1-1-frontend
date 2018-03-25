import struct

format_string = "2Q"
byte_length = 16
num_bytes = 100

with open('logs/lc1.log', 'rb') as f:
    for i in range(num_bytes):
        data = f.read(16)
        unpacked = struct.unpack(format_string, bytes(data))
        print (unpacked)