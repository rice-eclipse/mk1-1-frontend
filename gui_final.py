from collections import deque
from tkinter import PhotoImage
import matplotlib.pyplot as plt
from scipy import random
import tkinter as tk
import tkinter.ttk as ttk
from concurrency import async
from networking import*
import matplotlib.animation as animation
from server_info import ServerInfo
from graph_constants import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')


class GUIBackend:
    def __init__(self, queue_lc1s, queue_lc2s, queue_lc3s, queue_lc_mains, queue_tc1s, queue_tc2s, queue_tc3s,
                 queue_feed, queue_inje, queue_comb):

        self.nw_queue = Queue()
        self.nw = Networker(queue=self.nw_queue, loglevel=LogLevel.INFO)

        self.queues = [queue_lc1s, queue_lc2s, queue_lc3s, queue_lc_mains]
        self.Q_LC1S = queue_lc1s
        self.Q_LC2S = queue_lc2s
        self.Q_LC3S = queue_lc3s
        self.Q_LCMAINS = queue_lc_mains

        self.Q_TC1S = queue_tc1s
        self.Q_TC2S = queue_tc2s
        self.Q_TC3S = queue_tc3s

        self.Q_FEED = queue_feed
        self.Q_INJE = queue_inje
        self.Q_COMB = queue_comb

        # A dictionary to match received info to queues (see _process_recv_message)
        self.queue_dict = {
            ServerInfo.LC1S: self.Q_LC1S,
            ServerInfo.LC2S: self.Q_LC2S,
            ServerInfo.LC3S: self.Q_LC3S,
            ServerInfo.LC_MAINS: self.Q_LCMAINS,
            ServerInfo.TC1S: self.Q_TC1S,
            ServerInfo.TC2S: self.Q_TC2S,
            ServerInfo.TC3S: self.Q_TC3S,
            ServerInfo.PT_FEEDS: self.Q_FEED,
            ServerInfo.PT_COMBS: self.Q_COMB,
            ServerInfo.PT_INJES: self.Q_INJE
        }

        self.logger = Logger(name='GUI', level=LogLevel.INFO, outfile='gui.log')
        self._periodic_process_recv()

    def send_text(self, s):
        self.nw.send(str.encode(s))

    def send_num(self, i):
        self.nw.send(int.to_bytes(i, byteorder='big', length=4))

    def send_byte(self, b):
        self.nw.send(bytes([b]))

    def send(self, b):
        self.nw.send(b)

    def connect(self, address, port):
        self.nw.connect(addr=address, port=port)

    def ignite(self):
        self.nw.send(ServerInfo.NORM_IGNITE)

    @async
    def _periodic_process_recv(self):
        while True:
            time.sleep(0.1)
            if not self.nw.connected:
                continue

            self._process_recv_message()

    def _process_recv_message(self):
        """
        Processes new messages from nw_queue and give them to the appropriate GUI thread.
        """
        if self.nw_queue.qsize() > 0:
            self.logger.debug("Processing Messages")

        while self.nw_queue.qsize() > 0:
            mtype, nbytes, message = self.nw_queue.get()
            self.logger.debug("Processing message: Type:" + str(mtype) + " Nbytes:" + str(nbytes))

            # If the data size isn't what we expect, do nothing
            if nbytes % self.nw.server_info.info.payload_bytes != 0:
                self.logger.error("Received PAYLOAD message with improper number of bytes:" + str(nbytes))
                return
            else: # Check mtype to determine what to do
                if mtype == ServerInfo.ACK_VALUE:
                    pass
                elif mtype in ServerInfo.filenames.keys():
                    self.nw.server_info.read_payload(message, nbytes, self.queue_dict[mtype], mtype)
                elif mtype == ServerInfo.TEXT:
                    print(message.decode('utf-8'))
                    # sys.stdout.write(message.decode('utf-8'))
                else:
                    self.logger.error("Received incorrect message header type" + str(mtype))


class GUIFrontend():

    def __init__(self, backend):
        self.backend = backend
        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.root.wm_title("Rice Eclipse Mk-1.1 GUI")

        # Create a notebook and the tabs
        notebook = ttk.Notebook(self.root)
        default = ttk.Frame(notebook)
        logging = ttk.Frame(notebook)
        calibration = ttk.Frame(notebook)

        notebook.add(default, text='Default')
        notebook.add(logging, text='Logging')
        notebook.add(calibration, text='Calibration')
        notebook.grid(row=1, column=1, sticky='NW')

        # Potential to add styles
        s = ttk.Style()

        s.theme_create("BlueTabs", parent="default", settings={
            "TNotebook": {
                "configure": {"background": "#f0f8ff"},}})

        s.theme_use("default")

        # This figure contains everything to do with matplotlib on the left hand side
        figure, axes_list = plt.subplots(nrows=2, ncols=2)
        self.axes_list = list(axes_list[0]).append(axes_list[1])
        figure.subplots_adjust(top=.9, bottom=.1, left=.12, right=.95, wspace=.3, hspace=.5)
        figure.set_size_inches(8, 6)
        figure.set_dpi(100)

        # Create a canvas to show this figure under the default tab
        default_canvas = FigureCanvasTkAgg(figure, master=default)
        default_canvas.get_tk_widget().grid(row=1, column=1, sticky="NW")

        self.plots = [axes_list[0][0].plot([0], [0]),
                      axes_list[0][1].plot([0], [0]),
                      axes_list[1][0].plot([0], [0]),
                      axes_list[1][1].plot([0], [0])]

        self.plot_selections = ["LC_MAINS", "LC1S", "TC2S", "PT_INJE"]

        self.plot_datax = [deque(maxlen=1000), deque(maxlen=1000), deque(maxlen=10), deque(maxlen=100)]
        self.plot_datay = [deque(maxlen=1000), deque(maxlen=1000), deque(maxlen=10), deque(maxlen=100)]
        self.plot_points = [Queue(), Queue(), Queue(), Queue()]

        # NOTE: the graphs aren't synchronized right now because new data is generated every time the graph
        # is updated, and the graphs with less data update faster.
        # This shouldn't be a problem when we plot our actual data.
        self.animation = animation.FuncAnimation(figure, self.animate, interval=10)

        # This frame contains everything to do with buttons and entry boxes on the right hand side
        control_panel = tk.Frame(background="AliceBlue", width=350, height=625)
        control_panel.grid(row=1, column=2, sticky="NE")

        network_frame = tk.LabelFrame(control_panel, text="Network", background="AliceBlue")

        tk.ttk.Label(network_frame, text="IP", background="AliceBlue").grid(row=1 ,column=1, sticky="w", padx=15)
        tk.ttk.Label(network_frame, text="port", background="AliceBlue").grid(row=1, column=2, sticky="w", padx=15)

        ip_entry = tk.ttk.Entry(network_frame, width=15)
        ip_entry.insert(tk.END, '192.168.1.137')
        ip_entry.grid(row=2, column=1, padx=15)

        port_entry = tk.ttk.Entry(network_frame, width=5)
        port_entry.insert(tk.END, '1234')
        port_entry.grid(row=2, column=2, padx=15, sticky="w")

        network_frame.grid(row=1, column=1, pady=(15, 20))

        # Connect and disconnect buttons
        tk.ttk.Button(network_frame, text="Connect", command=lambda:backend.connect(ip_entry.get(), port_entry.get()))\
            .grid(row=3, column=1, pady=(15,10), padx=15, sticky="w")

        tk.ttk.Button(network_frame, text="Disconnect", command=lambda:backend.nw.disconnect())\
            .grid(row=3, column=2, pady=(15,10), padx=15)

        valve_frame = tk.LabelFrame(control_panel, text="Valve", background="AliceBlue")

        # Buttons for actuating the valve
        tk.ttk.Button(valve_frame, text="Set Valve", command=lambda:backend.send(ServerInfo.SET_VALVE))\
            .grid(row=1, column=1, padx=15, pady=10)

        tk.ttk.Button(valve_frame, text="Unset Valve", command=lambda:backend.send(ServerInfo.UNSET_VALVE))\
            .grid(row=1, column=2, padx=15, pady=10)

        valve_frame.grid(row=3, column=1, pady=25)

        ignition_frame = tk.LabelFrame(control_panel, text="Ignition", background="AliceBlue")

        tk.ttk.Label(ignition_frame, text="Burn Time", background="AliceBlue").grid(row=1, column=1, sticky="w", padx=15)
        tk.ttk.Label(ignition_frame, text="Delay", background="AliceBlue").grid(row=1, column=2, sticky="w", padx=15)

        burn_entry = tk.ttk.Entry(ignition_frame, width=6)
        burn_entry.insert(tk.END, '3')
        burn_entry.grid(row=2, column=1, padx=15, sticky="w")

        delay_entry = tk.ttk.Entry(ignition_frame, width=6)
        delay_entry.insert(tk.END, '0.5')
        delay_entry.grid(row=2, column=2, padx=15, sticky="w")

        # TODO send the ignition length to the backend when we press the button
        set_ignition_button = tk.ttk.Button(ignition_frame, text="IGNITE",
                                        command=lambda:backend.send(ServerInfo.SET_IGNITION))
        set_ignition_image = PhotoImage(file="ignite.gif")
        set_ignition_button.config(image=set_ignition_image)
        set_ignition_button.image = set_ignition_image
        set_ignition_button.grid(row=3, column=1, padx=15, pady=10)

        unset_ignition_button = tk.ttk.Button(ignition_frame, text="UNIGNITE",
                                          command=lambda: backend.send(ServerInfo.UNSET_IGNITION))
        unset_ignition_image = PhotoImage(file="unignite.gif")
        unset_ignition_button.config(image=unset_ignition_image)
        unset_ignition_button.image = unset_ignition_image
        unset_ignition_button.grid(row=3, column=2, padx=15, pady=10)

        ignition_frame.grid(row=4, column=1, pady=20)

        graph_frame = tk.LabelFrame(control_panel, text="Graphs", background="AliceBlue")

        choices = ["LC1S", "LC2S", "LC3S", "LC_MAINS", "PT_FEED", "PT_INJE", "PT_COMB", "TC1S", "TC2S", "TC3S"]
        self.graph_variables = [tk.StringVar(graph_frame), tk.StringVar(graph_frame),
                           tk.StringVar(graph_frame), tk.StringVar(graph_frame)]
        option_menus = []

        for i in range(4):
            option_menus.append(tk.ttk.OptionMenu(graph_frame, self.graph_variables[i], choices[0], *choices))
            option_menus[i].config(width=10)
            option_menus[i].grid(row=2 + 2 * int(i < 2), column=i % 2 + 1,  padx=15, pady=(0, 10))

        tk.Label(graph_frame, text="Top Left", background="AliceBlue").grid(row=1, column=1, sticky="w", padx=15)
        tk.Label(graph_frame, text="Top Right", background="AliceBlue").grid(row=1, column=2, sticky="w", padx=15)
        tk.Label(graph_frame, text="Bot Left", background="AliceBlue").grid(row=3, column=1, sticky="w", padx=15)
        tk.Label(graph_frame, text="Bot Right", background="AliceBlue").grid(row=3, column=2, sticky="w", padx=15)

        graph_frame.grid(row=2, column=1, pady=20)

    def animate(self, *fargs):
        # The backend logs and inserts data into queues after receiving stuff
        # Here we display what the user has selected
        for i in range(4):
            graph_selection = self.graph_variables[i].get()
            graph_selection_byte = str_to_byte[graph_selection]
            if (graph_selection == self.plot_selections[i]): # If the selection hasn't changed, just add the new points
                # Randomly generate some data to plot
                for j in range(1, 11):
                    self.plot_points[i].put((random.randint(0, 1000), self.plot_datax[i][-1] + j))

                while self.plot_points[i].qsize() > 1:
                    adc_data, t = self.plot_points[i].get()

                    self.plot_datax[i].append(t)
                    self.plot_datay[i].append(adc_data)

                # print ("name", self.name)
                # print ("xlist", self.xlist)
                # print ("ylist", self.ylist)
                # print (self.filename, "Avg of last 5 values: ", sum(self.ylist[-5:])/5.0)

            else: #Otherwise we need to reset all the data we're going to plot
                data_length = data_lengths[graph_selection]
                self.plot_datax[i] = deque(maxlen=data_length)
                self.plot_datay[i] = deque(maxlen=data_length)

                #todo maybe we should just update datax and datay constantly.
                for index in range(data_length):
                    adc_data, t = self.backend.queue_dict[graph_selection_byte].get()
                    self.plot_datax[i].append(t)
                    self.plot_datay[i].append(adc_data)

                # This is annoying, but we redraw the axes when we rescale so we have to set these again
                self.axes_list[i].set_title(graph_selection)
                self.axes_list[i].set_xlabel(labels[graph_selection][0])
                self.axes_list[i].set_ylabel(labels[graph_selection][1])

                # Update the data in our graph instead of drawing a new graph
                self.plots[i].set_xdata(self.plot_datax[i])
                self.plots[i].set_ydata(self.plot_datay[i])

                # Recalculate the x and y ranges. x will always change because it is time, but
                # only change y if we have new data that is out of bounds.
                self.axes_list[i].relim()
                if min(self.plot_datay[i]) < self.axes_list[i].get_ylim()[0] or \
                        max(self.plot_datay[i]) > self.axes_list[i].get_ylim()[1]:
                    self.axes_list[i].autoscale_view(scalex=True, scaley=True)
                else:
                    self.axes_list[i].autoscale_view(scalex=True, scaley=False)

            self.graph_variables[i] = graph_selection

frontend = GUIFrontend(GUIBackend(Queue(), Queue(), Queue(), Queue(), Queue(),
                                  Queue(), Queue(), Queue(), Queue(), Queue()))
frontend.root.mainloop()