"""
This file defines GUIFrontend, which contains real-time graphs for
sensor data and buttons for sending commands to the Pi. The backend
communicates with the frontend using a Back2FrontAdapter, which is
defined in GUIController.
"""

from tkinter import ttk

import Pmw
import tkinter as tk

from matplotlib import pyplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import AutoLocator
from matplotlib.transforms import Bbox

from gui_constants import data_lengths, samples_to_keep, str_to_byte, labels
from networking.server_info import ServerInfo


class GUIFrontend:
    """
    This class is responsible for organizing Tkinter widgets
    and matplotlib plots. Some of the ways we store and modify
    data are questionable, but optimizing this isn't really a
    priority.
    """

    def __init__(self, backend_adapter, config):
        self.backend_adapter = backend_adapter
        self.config = config

        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.width = 850
        self.height = 725
        self.dpi = 75
        self.root.configure(background="AliceBlue")
        self.root.wm_title("Rice Eclipse Mk-1.1 GUI")
        self.frame_delay_ms = round(1000 / int(self.config.get("Display", "Target Framerate")))

        Pmw.initialise(self.root)
        self.frame_count = 0
        self.frames_to_skip = int(self.config.get("Display", "Skip Frames for Axis Update"))
        self.plot_selections = ["LC_MAIN", "LC1", "TC2", "PT_INJE"]
        self.choices = list(labels.keys())

        self.notebook = self.init_tabs_container()
        self.init_calibration_tab()
        self.canvas, self.figure, self.plots, self.axes_list = self.init_graphs()
        self.graph_variables, self.fine_control, self.set_limits = self.init_mission_control_tab()
        self.data_logs, self.network_logs = self.init_logging_tab()
        self.graph_area = self.init_refresh_settings()

        # Update as soon as mainloop starts
        self.root.after(0, self.animate)

    def init_tabs_container(self):
        """
        Initializes the tabs container, which is a Notebook
        instance that contains Frames for each tab.
        @return: The notebook containing tabs.
        """
        notebook = ttk.Notebook(self.root)
        mission_control = ttk.Frame(notebook, name="mission_control")
        logging = ttk.Frame(notebook, name="logging")
        calibration = ttk.Frame(notebook, name="calibration")

        notebook.add(mission_control, text='Mission Control')
        notebook.add(logging, text='Logging')
        notebook.add(calibration, text='Calibration')
        notebook.grid(row=1, column=1, sticky='NW')

        # Potential to add styles
        s = ttk.Style()

        s.theme_create("BlueTabs", parent="default", settings={
            "TNotebook": {
                "configure": {"background": "#f0f8ff"}}})

        s.theme_use("default")

        return notebook

    def init_graphs(self):
        """
        Initializes the matplotlib graphs.
        @return: A list of the canvas and figure containing the graphs,
                 and a list of plots and axes of those plots.
        """
        figure, axes_list = pyplot.subplots(nrows=2, ncols=2)
        axes_list = axes_list.flatten()
        figure.subplots_adjust(top=.9, bottom=.1, left=.12, right=.95, wspace=.3, hspace=.5)
        figure.set_size_inches(float(self.width) / self.dpi, float(self.height) / self.dpi)
        figure.set_dpi(self.dpi)

        # Create a canvas to show this figure under the default tab
        canvas = FigureCanvasTkAgg(figure, master=self.notebook.nametowidget("mission_control"))
        canvas.get_tk_widget().grid(row=1, column=1, sticky="NW")

        # time = float(str(datetime.now().time()).split(":")[2])
        # print(time)
        # self.last_update = [time, time, time, time]
        plots = [axes_list[0].plot([0], [0])[0],
                 axes_list[1].plot([0], [0])[0],
                 axes_list[2].plot([0], [0])[0],
                 axes_list[3].plot([0], [0])[0]]

        # plt.setp(self.plots[0], aa=True)

        return canvas, figure, plots, axes_list

    def init_mission_control_tab(self):
        """
        Initializes the mission control tab, which contains widgets
        for connecting to an address and port, selecting which graphs
        to display, and starting ignition, among others.
        @return: Variables for graph selections, fine control, and data limits,
                 which affect what is displayed on other frames.
        """
        control_panel = tk.Frame(background="AliceBlue", width=350, height=625)
        control_panel.grid(row=1, column=2, sticky="NE")

        network_frame = tk.LabelFrame(control_panel, text="Network", background="AliceBlue")

        tk.ttk.Label(network_frame, text="IP", background="AliceBlue")\
            .grid(row=1, column=1, sticky="w", padx=15)
        tk.ttk.Label(network_frame, text="port", background="AliceBlue")\
            .grid(row=1, column=2, sticky="w", padx=15)

        ip_entry = tk.ttk.Entry(network_frame, width=15)
        ip_entry.insert(tk.END, self.config.get("UI Defaults", "Address"))
        ip_entry.grid(row=2, column=1, padx=15)

        port_entry = tk.ttk.Entry(network_frame, width=5)
        port_entry.insert(tk.END, self.config.get("UI Defaults", "Port"))
        port_entry.grid(row=2, column=2, padx=15, sticky="w")

        tk.ttk.Button(network_frame, text="Connect", command=lambda: self.backend_adapter.connect(
            ip_entry.get(), port_entry.get()))\
            .grid(row=3, column=1, pady=(15, 10), padx=15, sticky="w")

        tk.ttk.Button(network_frame, text="Disconnect", command=lambda: self.backend_adapter.disconnect()) \
            .grid(row=3, column=2, pady=(15, 10), padx=15)

        network_frame.grid(row=1, column=1, pady=(7, 10))

        # Frame for selection of graphs
        graph_frame = tk.LabelFrame(control_panel, text="Graphs", background="AliceBlue")

        graph_variables = [tk.StringVar(graph_frame), tk.StringVar(graph_frame),
                           tk.StringVar(graph_frame), tk.StringVar(graph_frame)]
        fine_control = tk.BooleanVar(graph_frame)
        set_limits = tk.BooleanVar(graph_frame)
        option_menus = []

        for i in range(4):
            option_menus.append(
                tk.ttk.OptionMenu(graph_frame, graph_variables[i], self.plot_selections[i], *self.choices))
            option_menus[i].config(width=10)
            option_menus[i].grid(row=2 + 2 * int(i > 1), column=i % 2 + 1, padx=10, pady=(0, 10))

        tk.Label(graph_frame, text="Top Left", background="AliceBlue").grid(row=1, column=1, sticky="w", padx=10)
        tk.Label(graph_frame, text="Top Right", background="AliceBlue").grid(row=1, column=2, sticky="w", padx=10)
        tk.Label(graph_frame, text="Bot Left", background="AliceBlue").grid(row=3, column=1, sticky="w", padx=10)
        tk.Label(graph_frame, text="Bot Right", background="AliceBlue").grid(row=3, column=2, sticky="w", padx=10)

        tk.ttk.Checkbutton(graph_frame, text="Show All Data", variable=fine_control) \
            .grid(row=5, column=1, sticky="w", padx=15, pady=(5, 15))

        tk.ttk.Checkbutton(graph_frame, text="Data Limits", variable=set_limits) \
            .grid(row=5, column=2, sticky="w", padx=15, pady=(5, 15))

        graph_frame.grid(row=2, column=1, pady=10)

        # Frame for controlling the valves
        valve_frame = tk.LabelFrame(control_panel, text="Valve", background="AliceBlue")

        tk.ttk.Button(valve_frame, text="Main On", command=lambda: self.backend_adapter.send(ServerInfo.SET_VALVE))\
            .grid(row=1, column=1, padx=15, pady=10)

        tk.ttk.Button(valve_frame, text="Main Off", command=lambda: self.backend_adapter.send(
                ServerInfo.UNSET_VALVE)) .grid(row=1, column=2, padx=15, pady=10)

        if self.config.get("Engine", "Engine") == "Titan":
            tk.ttk.Button(valve_frame, text="Vent On", command=lambda: self.backend_adapter.send(ServerInfo.SET_PVALVE)) \
                .grid(row=2, column=1, padx=15, pady=10)

            tk.ttk.Button(valve_frame, text="Vent Off", command=lambda: self.backend_adapter.send(
                    ServerInfo.UNSET_PVALVE)) .grid(row=2, column=2, padx=15, pady=10)

            tk.ttk.Button(valve_frame, text="Tank On", command=lambda: self.backend_adapter.send(ServerInfo.SET_GITVC)) \
                .grid(row=3, column=1, padx=15, pady=10)

            tk.ttk.Button(valve_frame, text="Tank Off", command=lambda: self.backend_adapter.send(
                    ServerInfo.UNSET_GITVC)) .grid(row=3, column=2, padx=15, pady=10)

            tk.ttk.Button(valve_frame, text="Leak Check", command=lambda: self.backend_adapter.send(
                    ServerInfo.LEAK_CHECK)) .grid(row=4, column=1, padx=15, pady=10)

            tk.ttk.Button(valve_frame, text="Fill", command=lambda: self.backend_adapter.send(ServerInfo.FILL)) \
                .grid(row=4, column=2, padx=15, pady=10)

            tk.ttk.Button(valve_frame, text="Fill Idle", command=lambda: self.backend_adapter.send(
                    ServerInfo.FILL_IDLE)) .grid(row=5, column=1, padx=15, pady=10)

            tk.ttk.Button(valve_frame, text="Default", command=lambda: self.backend_adapter.send(ServerInfo.DEFAULT)) \
                .grid(row=5, column=2, padx=15, pady=10)
        else:
            tk.ttk.Button(valve_frame, text="PValve", command=lambda: self.backend_adapter.send(ServerInfo.SET_PVALVE)) \
                .grid(row=2, column=1, padx=15, pady=10)

            tk.ttk.Button(valve_frame, text="End PValve", command=lambda: self.backend_adapter.send(
                    ServerInfo.UNSET_PVALVE)) .grid(row=2, column=2, padx=15, pady=10)

            tk.ttk.Button(valve_frame, text="GITVC", command=lambda: self.backend_adapter.send(ServerInfo.SET_GITVC)) \
                .grid(row=3, column=1, padx=15, pady=10)

            tk.ttk.Button(valve_frame, text="END_GITVC", command=lambda: self.backend_adapter.send(
                    ServerInfo.UNSET_GITVC)) .grid(row=3, column=2, padx=15, pady=10)

        valve_frame.grid(row=3, column=1, pady=10)

        # Frame for ignition
        ignition_frame = tk.LabelFrame(control_panel, text="Ignition", background="AliceBlue")

        # TODO send the ignition length to the backend when we press the button
        set_ignition_button = tk.ttk.Button(ignition_frame, text="IGNITE",
                                            command=lambda: self.backend_adapter.send(ServerInfo.NORM_IGNITE))
        set_ignition_image = tk.PhotoImage(file="resources/ignite.gif")
        set_ignition_button.config(image=set_ignition_image)
        set_ignition_button.image = set_ignition_image
        set_ignition_button.grid(row=3, column=1, padx=15, pady=10)

        unset_ignition_button = tk.ttk.Button(ignition_frame, text="UNIGNITE",
                                              command=lambda: self.backend_adapter.send(ServerInfo.UNSET_IGNITION))
        unset_ignition_image = tk.PhotoImage(file="resources/unignite.gif")
        unset_ignition_button.config(image=unset_ignition_image)
        unset_ignition_button.image = unset_ignition_image
        unset_ignition_button.grid(row=3, column=2, padx=15, pady=10)

        ignition_frame.grid(row=4, column=1, pady=15)

        return graph_variables, fine_control, set_limits

    def init_refresh_settings(self):
        """
        Initializes refresh settings that are used when
        blitting to relabel axes and other changes in the
        graph.
        @return: A graph_area for the graphs.
        """
        for i in range(4):
            self.axes_list[i].set_yticks([])
            self.axes_list[i].set_xticks([])
        self.canvas.draw()
        for i in range(4):
            self.axes_list[i].xaxis.set_major_locator(AutoLocator())
            self.axes_list[i].yaxis.set_major_locator(AutoLocator())
        [width, height] = self.canvas.get_width_height()
        graph_area = self.canvas.copy_from_bbox(Bbox.from_bounds(0, 0, width, height))

        return graph_area

    def init_logging_tab(self):
        """
        Initializes the logging (second) tab, which displays data values
        for each sensor and network log output.
        @return: The widgets that contain the log data.
        """
        data_logs = Pmw.ScrolledText(self.notebook.nametowidget("logging"),
                                     columnheader=1,
                                     usehullsize=1,
                                     hull_width=self.width,
                                     hull_height=350,
                                     text_wrap='none',
                                     Header_foreground='blue',
                                     Header_padx=4,
                                     hscrollmode='none',
                                     vscrollmode='none'
                                     )
        data_logs.tag_configure('yellow', background='yellow')

        # Create the column headers
        header_line = ''
        for column in range(len(self.choices)):
            header_line = header_line + self.choices[column] + ' ' * (10 - len(self.choices[column]))
        data_logs.component('columnheader').insert('0.0', header_line)
        data_logs.grid(row=1, column=1)

        network_logs = Pmw.ScrolledText(self.notebook.nametowidget("logging"),
                                        columnheader=1,
                                        usehullsize=1,
                                        hull_width=self.width,
                                        hull_height=self.height - 350,
                                        text_wrap='none',
                                        Header_foreground='blue',
                                        Header_padx=4,
                                        hscrollmode='none',
                                        vscrollmode='none'
                                        )

        network_logs.grid(row=2, column=1)

        return data_logs, network_logs

    def init_calibration_tab(self):
        """
        Initializes the calibration tab, which is used to conveniently
        store calibration data points and calculate the calibration curve.
        """
        calibration_frame = self.notebook.nametowidget('calibration')

        tk.Label(calibration_frame, text="Raw Value")\
            .grid(row=1, column=2, pady=10)

        tk.Label(calibration_frame, text="Actual Value") \
            .grid(row=3, column=2, pady=10)

        raw_value_entry = tk.ttk.Entry(calibration_frame, width=15)
        actual_value_entry = tk.ttk.Entry(calibration_frame, width=15)
        raw_value_entry.grid(row=2, column=2, pady=10)
        actual_value_entry.grid(row=4, column=2, pady=10)

        calib_display = Pmw.ScrolledText(calibration_frame,
                                         columnheader=1,
                                         usehullsize=1,
                                         hull_width=self.width,
                                         hull_height=350,
                                         text_wrap='none',
                                         Header_foreground='blue',
                                         Header_padx=4,
                                         hscrollmode='none',
                                         vscrollmode='none'
                                         )

        def add_action():
            """
            Action for the add button. Adds information to the display
            and adds the point in the backend.
            """
            calib_display.insert('end', "Raw value: {0}     Actual value: {1}\n"
                                 .format(raw_value_entry.get(), actual_value_entry.get()))
            self.backend_adapter.add_point((int(raw_value_entry.get()), int(actual_value_entry.get())))

        def clear_action():
            """
            Action for the clear button. Clears the displayed points
            and clears the stored points in the backend.
            """
            calib_display.clear()
            self.backend_adapter.clear_calibration()

        def get_action():
            """
            Action for the get button. Gets the calibration result
            from the backend and displays it.
            """
            slope, y_int = self.backend_adapter.get_calibration()
            calib_display.insert('end', "Slope: {0}     Y intercept: {1}\n"
                                 .format(slope, y_int))

        calib_display.grid(row=0, column=0, columnspan=6)
        tk.ttk.Button(calibration_frame, text="Add", command=add_action) \
            .grid(row=1, column=3, padx=15, pady=10)

        tk.ttk.Button(calibration_frame, text="Clear", command=clear_action) \
            .grid(row=2, column=3, padx=15, pady=10)

        tk.ttk.Button(calibration_frame, text="Get Calibration", command=get_action) \
            .grid(row=3, column=3, padx=15, pady=10)

    def animate(self):
        """
        The animation function for the GUI, which delegates
        to updating either the graphs or the log displays.
        """
        # Generate some random data to test plotting
        # for queue in self.backend_adapter.get_all_queues():
        #     length = len(queue) - 1
        #     for j in range(1, 11):
        #         queue.append((random.randint(0, 1000), queue[length][1] + j))

        if self.notebook.index(self.notebook.select()) == 0:
            self.draw_graphs()
        elif self.notebook.index(self.notebook.select()) == 1:
            self.update_log_displays()

        self.root.after(self.frame_delay_ms, self.animate)

    def draw_graphs(self):
        """
        Draws graphs using custom blitting and more fine-grain
        control of the frame rate.
        """
        for i in range(4):
            # Get which graph the user has selected and get the appropriate queue from the backend
            graph_selection = self.graph_variables[i].get()
            data_queue = self.backend_adapter.get_queue(str_to_byte[graph_selection])
            data_length = data_lengths[graph_selection]

            if self.fine_control.get():
                data_ratio = 1
            else:
                data_ratio = int(data_lengths[graph_selection] / samples_to_keep[graph_selection])
            # print (data_ratio)

            y_data = [cal for cal, t in data_queue[-data_length::data_ratio]]
            self.plots[i].set_xdata([t for cal, t in data_queue[-data_length::data_ratio]])
            self.plots[i].set_ydata(y_data)

            self.axes_list[i].relim()
            self.axes_list[i].autoscale_view()

        # Update auxiliary data in the graph.
        # i.e. stuff other than the line.
        self.canvas.restore_region(self.graph_area)
        self.frame_count = self.frame_count + 1
        if self.frame_count == self.frames_to_skip or self.frames_to_skip == 0:
            self.frame_count = 0
            update_axes = True
        else:
            update_axes = False
        for i in range(4):
            self.plots[i].axes.draw_artist(self.plots[i])
            if update_axes:
                self.plots[i].axes.draw_artist(self.axes_list[i].get_xaxis())
                self.plots[i].axes.draw_artist(self.axes_list[i].get_yaxis())
            else:
                self.canvas.blit(self.plots[i].axes.bbox)
        if update_axes:
            self.canvas.blit(self.plots[0].axes.clipbox)

    def update_log_displays(self):
        """
        Updates the sensor data part of the log displays.
        """
        self.data_logs.clear()
        # Create the data rows and the row headers
        num_rows = 20
        for row in range(1, num_rows):
            data_line = ''
            for column in range(len(self.choices)):
                # print(self.choices)
                data_queue = self.backend_adapter.get_queue(str_to_byte[self.choices[column]])
                value = str(data_queue[max(-len(data_queue) + 1, -num_rows + row)][0])[0:7]
                # print ("value", value)
                data_line = data_line + value + ' ' * (10 - len(value))
            data_line = data_line + '\n'
            self.data_logs.insert('end', data_line)

        averages = ''
        for column in range(len(self.choices)):
            data_queue = self.backend_adapter.get_queue(str_to_byte[self.choices[column]])
            avg = str(sum([cal for cal, t in data_queue[-num_rows:]]) / num_rows)[0:7]
            # data = str(average)[:9]
            # data = '%-7s' % (data,)
            averages = averages + avg + ' ' * (10 - len(avg))
        self.data_logs.insert('end', averages)
        self.data_logs.tag_add("yellow", '20.0', '20.' + str(len(averages)))

    def network_log_append(self, network_log_msg):
        """
        Appends a message to the network log display in the
        logging tab.
        @param network_log_msg: The message to append.
        """
        self.network_logs.insert('end', network_log_msg + '\n')

    def start(self):
        """
        Starts the frontend by starting the tkinter main loop.
        """
        self.root.mainloop()
