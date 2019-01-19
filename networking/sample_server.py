import socket
import threading
import time
from select import select


def main():
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

    def re_listen():
        tcp_socket.listen(1)
        tcp_socket.setblocking(True)
        conn, addr = tcp_socket.accept()
        print("Received tcp connection", conn)
        tcp_socket.setblocking(False)
        in_fds.append(conn)

    i = 0
    timestamp = 0
    header_type = 9
    nbytes = 16
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

                    thread = threading.Thread(target=re_listen)
                    thread.daemon = True
                    thread.start()

                else:
                    print("received:", str(data).upper())
            except ConnectionResetError:
                # When client is closed without closing the connection
                in_fds.remove(fd)
                fd.close()
                print("Connection reset")

                thread = threading.Thread(target=re_listen)
                thread.daemon = True
                thread.start()

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
            # fd.sendto(pad.to_bytes(8, byteorder='little'), (host, port))

            i = (i + 10) % 1000
            timestamp = timestamp + 1

        time.sleep(.001)


if __name__ == '__main__':
    main()
