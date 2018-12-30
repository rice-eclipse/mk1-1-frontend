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
    print ("Received tcp connection", conn)

    udp_socket.setblocking(False)
    tcp_socket.setblocking(False)

    in_fds = [conn]
    out_fds = [udp_socket]

    i = 0
    timestamp = 0
    while True:
        _input, _output, _except = select(in_fds, out_fds, [])

        for fd in _input:
            try:
                data=fd.recv(1024)
                data=data.decode()
                if not data:
                    # When client quits and closes connection
                    in_fds.remove(fd)
                    fd.close()
                    print ("Client connection has been closed")


                    def re_listen():
                        tcp_socket.listen(1)
                        tcp_socket.setblocking(True)
                        conn, addr = tcp_socket.accept()
                        print ("Received tcp connection", conn)
                        tcp_socket.setblocking(False)
                        in_fds.append(conn)

                    thread = threading.Thread(target=re_listen)
                    thread.daemon = True
                    thread.start()

                else:
                    print("received:", str(data).upper())
            except ConnectionResetError:
                # When client is closed without closing the connection
                print ("Connection reset")
                in_fds.remove(fd)
                fd.close()

        for fd in _output:
            fd.sendto(i.to_bytes(2, byteorder='big'), (host, port))
            fd.sendto(timestamp.to_bytes(8, byteorder='big'), (host, port))
            time.sleep(0.05)
            i = (i + 1) % 100
            timestamp = timestamp + 1

        time.sleep(.01)


if __name__ == '__main__':
    main()
