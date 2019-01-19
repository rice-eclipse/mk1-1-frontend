"""
This file defines a sample server that sends over UDP
and receives ove TCP using select. It can be used to
test the networker used in GUIBackend.
"""

import socket
import time
from select import select

from concurrency import run_async


def main():
    """
    Initializes sockets and select sets.
    Defines re_listen() which is used for safe reconnection.
    Sends/receives indefinitely over the two sockets.
    """
    host = "127.0.0.1"
    port = 1234

    udp_socket = socket.socket(type=socket.SOCK_DGRAM)
    tcp_socket = socket.socket(type=socket.SOCK_STREAM)

    # udp_socket.bind((host, port))
    tcp_socket.bind((host, port))

    tcp_socket.listen(1)
    conn, addr = tcp_socket.accept()
    print("Received tcp connection", conn)

    udp_socket.setblocking(False)
    tcp_socket.setblocking(False)

    in_fds = [conn]
    out_fds = [udp_socket]

    @run_async
    def re_listen():
        """
        Wraps socket listening code in a new thread and runs
        it. Allows TCP to accept a new client without affecting
        UDP.
        """
        tcp_socket.listen(1)
        tcp_socket.setblocking(True)
        new_conn, _ = tcp_socket.accept()
        print("Received tcp connection", conn)
        tcp_socket.setblocking(False)
        in_fds.append(new_conn)

    i = 0
    timestamp = 0
    header_type = 9    # Main load cell
    nbytes = 16        # Hard-coded for now. See OtherInfo in server_info.py
    pad = 0

    while True:
        _input, _output, _except = select(in_fds, out_fds, [])

        for fd in _input:
            try:
                data = fd.recv(1024)
                data = data.decode()
                if not data:
                    # When client quits and closes connection
                    in_fds.remove(fd)
                    fd.close()
                    print("Client connection has been closed")

                    re_listen()

                else:
                    print("received:", str(data).upper())
            except ConnectionResetError:
                # When client is closed without closing the connection
                in_fds.remove(fd)
                fd.close()
                print("Connection reset")

                re_listen()

        for fd in _output:
            # Send a header
            fd.sendto(header_type.to_bytes(1, byteorder='little'), (host, port))
            fd.sendto(pad.to_bytes(7, byteorder='little'), (host, port))
            fd.sendto(nbytes.to_bytes(4, byteorder='little'), (host, port))
            fd.sendto(pad.to_bytes(4, byteorder='little'), (host, port))

            time.sleep(0.05)

            # Send some data
            fd.sendto(i.to_bytes(2, byteorder='little'), (host, port))
            fd.sendto(pad.to_bytes(6, byteorder='little'), (host, port))
            fd.sendto(timestamp.to_bytes(8, byteorder='little'), (host, port))

            # Old code for use with sample_client.py
            # fd.sendto(i.to_bytes(2, byteorder='big'), (host, port))
            # fd.sendto(timestamp.to_bytes(8, byteorder='big'), (host, port))
            # time.sleep(0.05)

            i = (i + 10) % 1000
            timestamp = timestamp + 1

        time.sleep(.001)


if __name__ == '__main__':
    main()
