from tkinter import PhotoImage
import matplotlib.pyplot as plt
import tkinter as tk
import Pmw
import random
import tkinter.ttk as ttk
from concurrency import async
from networking import*
import matplotlib.animation as animation
from gui_constants import *
# from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class GUIBackend:
    def __init__(self, queue_lc1_send, queue_lc2_send, queue_lc3_send, queue_lc_main_send, queue_tc1_send,
                 queue_tc2_send, queue_tc3_send, queue_feed_send, queue_inje_send, queue_comb_send):

        self.nw_queue = Queue()
        self.nw = Networker(queue=self.nw_queue, loglevel=LogLevel.INFO)

        self.Q_LC1 = queue_lc1_send
        self.Q_LC2 = queue_lc2_send
        self.Q_LC3 = queue_lc3_send
        self.Q_LC_MAIN = queue_lc_main_send

        self.Q_TC1 = queue_tc1_send
        self.Q_TC2 = queue_tc2_send
        self.Q_TC3 = queue_tc3_send

        self.Q_FEED = queue_feed_send
        self.Q_INJE = queue_inje_send
        self.Q_COMB = queue_comb_send

        self.queues = [self.Q_LC1, self.Q_LC2, self.Q_LC3, self.Q_LC_MAIN, self.Q_TC1,
                       self.Q_TC2, self.Q_TC3, self.Q_FEED, self.Q_INJE, self.Q_COMB]

        for queue in self.queues:
            queue.append((0, 0))

        # A dictionary to match mtypes to queues (see _process_recv_message)
        self.queue_dict = {
            ServerInfo.LC1_SEND: self.Q_LC1,
            ServerInfo.LC2_SEND: self.Q_LC2,
            ServerInfo.LC3_SEND: self.Q_LC3,
            ServerInfo.LC_MAIN_SEND: self.Q_LC_MAIN,
            ServerInfo.TC1_SEND: self.Q_TC1,
            ServerInfo.TC2_SEND: self.Q_TC2,
            ServerInfo.TC3_SEND: self.Q_TC3,
            ServerInfo.PT_FEED_SEND: self.Q_FEED,
            ServerInfo.PT_COMB_SEND: self.Q_COMB,
            ServerInfo.PT_INJE_SEND: self.Q_INJE
        }

        self.gui_logs = ["GUI Logs Ready"]
        self.logger = Logger(name='GUI', log_list=self.gui_logs, level=LogLevel.INFO, outfile='gui.log')
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
        self.nw.update_server_info(addr=address)
        self.nw.connect(addr=address, port=port)

    def ignite(self):
        # todo send some numbers over
        self.logger.error("IGNITING!!!")
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
            else:  # Check mtype to determine what to do
                if mtype == ServerInfo.ACK_VALUE:
                    pass
                elif mtype in ServerInfo.filenames.keys():
                    self.nw.server_info.read_payload(message, nbytes, self.queue_dict[mtype], mtype)
                elif mtype == ServerInfo.TEXT:
                    print(message.decode('utf-8'))
                    # sys.stdout.write(message.decode('utf-8'))
                else:
                    self.logger.error("Received incorrect message header type" + str(mtype))


class GUIFrontend:
    def __init__(self, backend):
        self.backend = backend
        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.root.wm_title("Rice Eclipse Mk-1.1 GUI")
        self.refresh_rate = 1 # In seconds

        Pmw.initialise(self.root)

        # Create a notebook and the tabs
        self.notebook = ttk.Notebook(self.root)
        mission_control = ttk.Frame(self.notebook)
        logging = ttk.Frame(self.notebook)
        calibration = ttk.Frame(self.notebook)

        self.notebook.add(mission_control, text='Mission Control')
        self.notebook.add(logging, text='Logging')
        self.notebook.add(calibration, text='Calibration')
        self.notebook.grid(row=1, column=1, sticky='NW')

        # Potential to add styles
        s = ttk.Style()

        s.theme_create("BlueTabs", parent="default", settings={
            "TNotebook": {
                "configure": {"background": "#f0f8ff"}}})

        s.theme_use("default")

        # This figure contains everything to do with matplotlib on the left hand side
        self.figure, axes_list = plt.subplots(nrows=2, ncols=2)
        self.axes_list = list(axes_list[0]) + list(axes_list[1])
        self.figure.subplots_adjust(top=.9, bottom=.1, left=.12, right=.95, wspace=.3, hspace=.5)
        self.figure.set_size_inches(8, 6)
        self.figure.set_dpi(100)

        # Create a canvas to show this figure under the default tab
        default_canvas = FigureCanvasTkAgg(self.figure, master=mission_control)
        default_canvas.get_tk_widget().grid(row=1, column=1, sticky="NW")

        # time = float(str(datetime.now().time()).split(":")[2])
        # print(time)
        # self.last_update = [time, time, time, time]
        self.plots = [axes_list[0][0].plot([0], [0])[0],
                      axes_list[0][1].plot([0], [0])[0],
                      axes_list[1][0].plot([0], [0])[0],
                      axes_list[1][1].plot([0], [0])[0]]

        # plt.setp(self.plots[0], aa=True)

        self.plot_selections = ["LC_MAIN", "LC1", "TC2", "PT_INJE"]

        self.animation = animation.FuncAnimation(self.figure, self.animate, interval=500)

        # This frame contains everything to do with buttons and entry boxes on the right hand side
        control_panel = tk.Frame(background="AliceBlue", width=350, height=625)
        control_panel.grid(row=1, column=2, sticky="NE")

        network_frame = tk.LabelFrame(control_panel, text="Network", background="AliceBlue")

        tk.ttk.Label(network_frame, text="IP", background="AliceBlue").grid(row=1, column=1, sticky="w", padx=15)
        tk.ttk.Label(network_frame, text="port", background="AliceBlue").grid(row=1, column=2, sticky="w", padx=15)

        ip_entry = tk.ttk.Entry(network_frame, width=15)
        ip_entry.insert(tk.END, '192.168.1.137')
        ip_entry.grid(row=2, column=1, padx=15)

        port_entry = tk.ttk.Entry(network_frame, width=5)
        port_entry.insert(tk.END, '1234')
        port_entry.grid(row=2, column=2, padx=15, sticky="w")

        tk.ttk.Button(network_frame, text="Connect", command=lambda: backend.connect(ip_entry.get(), port_entry.get()))\
            .grid(row=3, column=1, pady=(15, 10), padx=15, sticky="w")
        tk.ttk.Button(network_frame, text="Disconnect", command=lambda: backend.nw.disconnect()) \
            .grid(row=3, column=2, pady=(15, 10), padx=15)

        network_frame.grid(row=1, column=1, pady=(7, 20))

        # Frame for selection of graphs
        graph_frame = tk.LabelFrame(control_panel, text="Graphs", background="AliceBlue")

        self.choices = ["LC1", "LC2", "LC3", "LC_MAIN", "PT_FEED", "PT_INJE", "PT_COMB", "TC1", "TC2", "TC3"]
        self.graph_variables = [tk.StringVar(graph_frame), tk.StringVar(graph_frame),
                                tk.StringVar(graph_frame), tk.StringVar(graph_frame)]
        self.fine_control = tk.BooleanVar(graph_frame)
        self.set_limits = tk.BooleanVar(graph_frame)
        option_menus = []

        for i in range(4):
            option_menus.append(
                tk.ttk.OptionMenu(graph_frame, self.graph_variables[i], self.plot_selections[i], *self.choices))
            option_menus[i].config(width=10)
            option_menus[i].grid(row=2 + 2 * int(i > 1), column=i % 2 + 1, padx=10, pady=(0, 10))

        tk.Label(graph_frame, text="Top Left", background="AliceBlue").grid(row=1, column=1, sticky="w", padx=10)
        tk.Label(graph_frame, text="Top Right", background="AliceBlue").grid(row=1, column=2, sticky="w", padx=10)
        tk.Label(graph_frame, text="Bot Left", background="AliceBlue").grid(row=3, column=1, sticky="w", padx=10)
        tk.Label(graph_frame, text="Bot Right", background="AliceBlue").grid(row=3, column=2, sticky="w", padx=10)

        tk.ttk.Checkbutton(graph_frame, text="Show All Data", variable=self.fine_control) \
            .grid(row=5, column=1, sticky="w", padx=15, pady=(5, 15))

        tk.ttk.Checkbutton(graph_frame, text="Data Limits", variable=self.set_limits) \
            .grid(row=5, column=2, sticky="w", padx=15, pady=(5, 15))

        graph_frame.grid(row=2, column=1, pady=15)

        # Frame for controlling the valves
        valve_frame = tk.LabelFrame(control_panel, text="Valve", background="AliceBlue")

        tk.ttk.Button(valve_frame, text="Set Valve", command=lambda: backend.send(ServerInfo.SET_VALVE))\
            .grid(row=1, column=1, padx=15, pady=10)

        tk.ttk.Button(valve_frame, text="Unset Valve", command=lambda: backend.send(ServerInfo.UNSET_VALVE))\
            .grid(row=1, column=2, padx=15, pady=10)

        tk.ttk.Button(valve_frame, text="GITVC", command=lambda: backend.send(ServerInfo.GITVC))\
            .grid(row=2, column=1, padx=15, pady=10)

        valve_frame.grid(row=3, column=1, pady=15)

        # Frame for ignition
        ignition_frame = tk.LabelFrame(control_panel, text="Ignition", background="AliceBlue")

        tk.ttk.Label(ignition_frame, text="Burn Time", background="AliceBlue")\
            .grid(row=1, column=1, sticky="w", padx=15)
        tk.ttk.Label(ignition_frame, text="Delay", background="AliceBlue").grid(row=1, column=2, sticky="w", padx=15)

        self.burn_entry = tk.ttk.Entry(ignition_frame, width=6)
        self.burn_entry.insert(tk.END, '3')
        self.burn_entry.grid(row=2, column=1, padx=15, sticky="w")

        self.delay_entry = tk.ttk.Entry(ignition_frame, width=6)
        self.delay_entry.insert(tk.END, '0.5')
        self.delay_entry.grid(row=2, column=2, padx=15, sticky="w")

        # TODO send the ignition length to the backend when we press the button
        set_ignition_button = tk.ttk.Button(ignition_frame, text="IGNITE",
                                            command=lambda: backend.send(ServerInfo.NORM_IGNITE))
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

        ignition_frame.grid(row=4, column=1, pady=(20, 10))

        self.st = Pmw.ScrolledText(logging,
                                   columnheader=1,
                                   usehullsize=1,
                                   hull_width=800,
                                   hull_height=350,
                                   text_wrap='none',
                                   Header_foreground='blue',
                                   Header_padx=4,
                                   hscrollmode='none',
                                   vscrollmode='none'
                                   )
        self.st.tag_configure('yellow', background='yellow')

        # Create the column headers
        header_line = ''
        for column in range(len(self.choices)):
            header_line = header_line + self.choices[column] + ' ' * (10 - len(self.choices[column]))
        self.st.component('columnheader').insert('0.0', header_line)
        self.st.grid(row=1, column=1)

        self.log_output = Pmw.ScrolledText(logging,
                                           columnheader=1,
                                           usehullsize=1,
                                           hull_width=800,
                                           hull_height=250,
                                           text_wrap='none',
                                           Header_foreground='blue',
                                           Header_padx=4,
                                           hscrollmode='none',
                                           vscrollmode='none'
                                           )

        self.log_output.grid(row=2, column=1)

    def animate(self, *fargs):
        # Randomly generate some data to plot
        # for queue in self.backend.queues:
            # length = len(queue) - 1
            # for j in range(1, 11):
                # queue.append((random.randint(0, 30) * 1.123456789, queue[length][1] + j))
            # print (queue)
        # print (self.backend.queues[0][-10:])

        # Only graph if we are on the mission control tab
        if self.notebook.index(self.notebook.select()) == 0:
            self.update_graphs()
        elif self.notebook.index(self.notebook.select()) == 1:
            self.update_log_displays()

    def update_graphs(self):

        # time_now = float(str(datetime.now().time()).split(":")[2])
        for i in range(4):
            # Get which graph the user has selected and get the appropriate queue from the backend
            graph_selection = self.graph_variables[i].get()
            data_queue = self.backend.queue_dict[str_to_byte[graph_selection]]
            data_length = data_lengths[graph_selection]

            if self.fine_control.get():
                data_ratio = 1
            else:
                data_ratio = int(data_lengths[graph_selection] / samples_to_keep[graph_selection])

            y_data = [cal for cal, t in data_queue[-data_length::data_ratio]]
            self.plots[i].set_xdata([t for cal, t in data_queue[-data_length::data_ratio]])
            self.plots[i].set_ydata(y_data)

            # print(time_now)
            # if time_now - self.last_update[i] > self.refresh_rate:
            self.axes_list[i].relim()
            self.axes_list[i].set_ylim(auto=True) # In case ylim was set to a lower value for a different sensor

            if self.set_limits.get() and max(y_data) > data_limits[graph_selection]:
                self.axes_list[i].set_ylim(ymax=data_limits[graph_selection])

            self.axes_list[i].autoscale_view()
            # self.last_update[i] = time_now

            # We have to do this even if we don't change graphs because the labels get erased after we scale the axes
            self.axes_list[i].set_title(graph_selection)
            self.axes_list[i].set_xlabel(labels[graph_selection][0])
            self.axes_list[i].set_ylabel(labels[graph_selection][1])

            self.plot_selections[i] = graph_selection

    def update_log_displays(self):
        self.st.clear()
        # Create the data rows and the row headers
        num_rows = 20
        for row in range(1, num_rows):
            data_line = ''
            for column in range(len(self.choices)):
                # print(self.choices)
                data_queue = self.backend.queue_dict[str_to_byte[self.choices[column]]]
                value = str(data_queue[max(-len(data_queue) + 1, -num_rows + row)][0])[0:7]
                # print ("value", value)
                data_line = data_line + value + ' ' * (10 - len(value))
            data_line = data_line + '\n'
            self.st.insert('end', data_line)

        averages = ''
        for column in range(len(self.choices)):
            data_queue = self.backend.queue_dict[str_to_byte[self.choices[column]]]
            avg = str(sum([cal for cal, t in data_queue[-num_rows:]]) / num_rows)[0:7]
            # data = str(average)[:9]
            # data = '%-7s' % (data,)
            averages = averages + avg + ' ' * (10 - len(avg))
        self.st.insert('end', averages)
        self.st.tag_add("yellow", '20.0', '20.' + str(len(averages)))

        # Logging output for the gui
        for i in range(len(self.backend.gui_logs)):
            self.log_output.insert('end', self.backend.gui_logs[i] + '\n')
        self.backend.gui_logs.clear()

        for i in range(len(self.backend.nw.network_logs)):
            self.log_output.insert('end', self.backend.nw.network_logs[i] + '\n')
        self.backend.nw.network_logs.clear()


frontend = GUIFrontend(GUIBackend([], [], [], [], [], [], [], [], [], []))
frontend.root.mainloop()
