import struct
from networking.server_info import ServerInfo

"""
File for converting binary logs on the Pi into human-readable logs. The format string
is hard-coded based on the format of the data written to the binary logs.
"""

format_string = "2Q"
mtype = ServerInfo.LC1_SEND
read_filepath = "PiLogs/"
write_filepath = "PiLogs/"
filenames = ["lc_main", "lc1", "lc2", "lc3", "pt_feed", "pt_inje", "pt_comb", "tc1", "tc2", "tc3"]


for i in range(10):
    filename = filenames[i]
    mtype = bytes([9 + i])

    with open(read_filepath + filename + '.log', 'rb') as f, open(write_filepath + filename + '_Pi.log', 'w') as p:

        f.seek(0, 2)
        file_size = f.tell()
        f.seek(0, 0)

        for i in range(int(file_size / 16)):
            data_line = f.read(16)
            d, t = struct.unpack(format_string, bytes(data_line))

            if mtype in ServerInfo.calibrations.keys():
                calib = ServerInfo.calibrations[mtype]
                cal = d * calib[0] + calib[1]
            else:
                print ("Bad Calibration")
                cal = 0

            p.write(str(t) + " " + str(d) + " " + str(cal) + "\n")
