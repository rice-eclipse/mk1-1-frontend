# right now only one plot is gonna be displayed; just add more if necessary

import socket
import threading
import tkinter as tk
from queue import Queue

import matplotlib
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

matplotlib.use("TKAgg")

udp = socket.socket(type=socket.SOCK_DGRAM)
tcp = socket.socket(type=socket.SOCK_STREAM)

# data buffer
y_data = Queue()
x_data = Queue()
x_data.put(0)

# plot style
style.use("dark_background")

# configure the plot
f = Figure(figsize=(5, 5), dpi=100)
plot = f.add_subplot(111)
xlist = []
ylist = []
plot.plot(xlist, ylist)


def animate(i):
    # while not x_data.empty():
    #     print("x")
    #     xlist.append(x_data.get())
    #
    # while not y_data.empty():
    #     print("y")
    #     ylist.append(y_data.get())

    plot.relim()
    plot.clear()
    plot.plot(xlist, ylist)


def socketread(s):
    while 1:
        data, _ = s.recvfrom(2)
        timestamp, _ = s.recvfrom(8)
        if len(timestamp) != 0 and len(data) != 0:
            timestamp_int = int.from_bytes(timestamp, byteorder='big', signed=True)
            data_int = int.from_bytes(data, byteorder='big', signed=True)
            xlist.append(timestamp_int)
            ylist.append(data_int)
            # print("timestamp:", timestamp_int)
            # print("data:", data_int)


# thread for data acquisition
class myThread1(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        socketread(udp)


# gui set up
class gui(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        frame_parent = tk.Frame(self)
        frame_parent.grid()
        # frame_parent.pack(side="top", fill="both", expand=True)
        frame_parent.grid_rowconfigure(0, weight=1)
        frame_parent.grid_columnconfigure(0, weight=1)

        label_ip = tk.Label(frame_parent, text="IP")
        label_ip.grid(row=0, column=0, padx=(5, 5))

        label_port = tk.Label(frame_parent, text="port")
        label_port.grid(row=0, column=2, padx=(10, 5))

        entry_host = tk.Entry(frame_parent)
        entry_host.insert(tk.END, "127.0.0.1")
        entry_host.grid(row=0, column=1, padx=(5, 10))

        entry_port = tk.Entry(frame_parent)
        entry_port.grid(row=0, column=3, padx=(5, 5))
        entry_port.insert(tk.END, "1234")

        entry_send = tk.Entry(frame_parent)
        entry_send.grid(row=1, column=3)

        tk.Button(frame_parent, text="Connect", command=lambda: connect_socket(entry_host.get(), entry_port.get())) \
            .grid(row=0, column=4, padx=(20, 5), pady=5)

        tk.Button(frame_parent, text="Send", command=lambda: send(entry_send.get())) \
            .grid(row=1, column=4, pady=5)

        # Canvas for matplotlib
        canvas = FigureCanvasTkAgg(f, self)
        canvas.get_tk_widget().grid(row=2, column=0, padx=5, pady=5, sticky="WENS")

    def run(self):
        self.mainloop()


# function to connect the socket
def connect_socket(host, port):
    udp.bind((host, int(port)))
    tcp.connect((host, int(port)))
    # Start listening on UDP. Only send on TCP when a button is pressed.
    thread1 = myThread1(1, "Thread-1", 1)
    thread1.start()


def send(entry):
    print("sending:", str.encode(entry))
    tcp.send(str.encode(entry))
    tcp.send(str.encode("\n"))


gui1 = gui()
ani = animation.FuncAnimation(f, animate, interval=100)
gui1.run()
