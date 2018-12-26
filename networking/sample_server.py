import socket
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
    print ("after accept")

    udp_socket.setblocking(False)
    tcp_socket.setblocking(False)

    in_fds = [tcp_socket]
    out_fds = [udp_socket]

    i = 0
    timestamp = 0
    while True:
        _input, _output, _except = select(in_fds, out_fds, [])

        for fd in _input:
            print ("receiving data")
            data=fd.recv(1024)
            data=data.decode()
            if not data:
                fd.close()
                return None
            print("from client"+str(data).upper())

        for fd in _output:
            fd.sendto(i.to_bytes(2, byteorder='big'), (host, port))
            fd.sendto(timestamp.to_bytes(8, byteorder='big'), (host, port))
            time.sleep(0.05)
            i = (i + 1) % 1000
            timestamp = timestamp + 1


if __name__ == '__main__':
    main()
