import random
from tkinter import ttk

import Pmw
import tkinter as tk

from matplotlib import pyplot, animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import AutoLocator
from matplotlib.transforms import Bbox

from gui_constants import data_lengths, samples_to_keep, str_to_byte, data_limits, labels
from networking.server_info import ServerInfo


class GUIFrontend:
    def __init__(self, backend_adapter, config):
        self.backend_adapter = backend_adapter
        self.config = config

        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.width = 850
        self.height = 625
        self.dpi = 75
        self.root.configure(background="AliceBlue")
        self.root.wm_title("Rice Eclipse Mk-1.1 GUI")
        self.refresh_rate = 1  # In seconds
        self.frame_delay_ms = round(1000 / int(self.config.get("Display", "Target Framerate")))

        Pmw.initialise(self.root)

#        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.frame_count = 0
        self.frames_to_skip = int(self.config.get("Display", "Skip Frames for Axis Update"))
        self.plot_selections = ["LC_MAIN", "LC1", "TC2", "PT_INJE"]
        self.choices = list(ServerInfo.filenames.values())

        self.notebook = self.init_tabs_container()
        self.canvas, self.figure, self.plots, self.axes_list = self.init_graphs()
        self.graph_variables, self.fine_control, self.set_limits = self.init_mission_control_tab()
        self.data_logs, self.network_logs = self.init_logging_tab()
        self.updater, self.graph_area = self.init_refresh_settings()
        self.root.after(0, self.draw_graphs())

    def init_tabs_container(self):
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
        control_panel = tk.Frame(background="AliceBlue", width=350, height=625)
        control_panel.grid(row=1, column=2, sticky="NE")

        network_frame = tk.LabelFrame(control_panel, text="Network", background="AliceBlue")

        tk.ttk.Label(network_frame, text="IP", background="AliceBlue").grid(row=1, column=1, sticky="w", padx=15)
        tk.ttk.Label(network_frame, text="port", background="AliceBlue").grid(row=1, column=2, sticky="w", padx=15)

        ip_entry = tk.ttk.Entry(network_frame, width=15)
        ip_entry.insert(tk.END, self.config.get("UI Defaults", "Address"))
        ip_entry.grid(row=2, column=1, padx=15)

        port_entry = tk.ttk.Entry(network_frame, width=5)
        port_entry.insert(tk.END, self.config.get("UI Defaults", "Port"))
        port_entry.grid(row=2, column=2, padx=15, sticky="w")

        tk.ttk.Button(network_frame, text="Connect", command=lambda: self.backend_adapter.connect(ip_entry.get(), port_entry.get()))\
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

        tk.ttk.Button(valve_frame, text="Set Valve", command=lambda: self.backend_adapter.send(ServerInfo.SET_VALVE))\
            .grid(row=1, column=1, padx=15, pady=10)

        tk.ttk.Button(valve_frame, text="Unset Valve", command=lambda: self.backend_adapter.send(ServerInfo.UNSET_VALVE))\
            .grid(row=1, column=2, padx=15, pady=10)

        tk.ttk.Button(valve_frame, text="Water", command=lambda: self.backend_adapter.send(ServerInfo.SET_WATER)) \
            .grid(row=2, column=1, padx=15, pady=10)

        tk.ttk.Button(valve_frame, text="End Water", command=lambda: self.backend_adapter.send(ServerInfo.UNSET_WATER)) \
            .grid(row=2, column=2, padx=15, pady=10)

        tk.ttk.Button(valve_frame, text="GITVC", command=lambda: self.backend_adapter.send(ServerInfo.SET_GITVC)) \
            .grid(row=3, column=1, padx=15, pady=10)

        tk.ttk.Button(valve_frame, text="END_GITVC", command=lambda: self.backend_adapter.send(ServerInfo.UNSET_GITVC)) \
            .grid(row=3, column=2, padx=15, pady=10)

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
        # plt.show()
        self.canvas.draw()
        if self.config.get("Display", "Use matplotlib Animation") == "True":
            blit = self.config.get("Display", "Blit") == "True"
            updater = animation.FuncAnimation(self.figure, self.animate, interval=self.frame_delay_ms, blit=blit)
            graph_area = None
        else:
            # tmp_xtick = []
            for i in range(4):
                # tmp_xtick.append(self.axes_list[i].get_xticklabels())
                self.axes_list[i].set_yticks([])
                self.axes_list[i].set_xticks([])
            self.canvas.draw()
            for i in range(4):
                # tmp_xtick.append(self.axes_list[i].get_xticklabels())
                self.axes_list[i].xaxis.set_major_locator(AutoLocator())
                self.axes_list[i].yaxis.set_major_locator(AutoLocator())
            # self.axes_list[0].set_xticklabels(tmp_xtick[0])
            [width, height] = self.canvas.get_width_height()
            graph_area = self.canvas.copy_from_bbox(Bbox.from_bounds(0, 0, width, height))
            # self.graphArea = self.canvas.copy_from_bbox(self.plots[0].axes.bbox)
            # print(self.plots[0].axes.bbox)
            # print(self.plots[1].axes.bbox)
            # self.root.after(0, self.draw_graphs())
            updater = None

        return updater, graph_area

    def init_logging_tab(self):
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
        # todo
        pass

    def animate(self, *args):
        # Randomly generate some data to plot
        for queue in self.backend_adapter.get_all_queues():
            length = len(queue) - 1
            for j in range(1, 11):
                queue.append((random.randint(0, 1000), queue[length][1] + j))
                # queue.append((queue[length][1] + j, queue[length][1] + j))
            # print (queue)
        # print (self.backend.queues[0][-10:])

        # Only graph if we are on the mission control tab
        if self.notebook.index(self.notebook.select()) == 0:
            return self.update_graphs()
        elif self.notebook.index(self.notebook.select()) == 1:
            self.update_log_displays()

    def draw_graphs(self):
        self.root.after(self.frame_delay_ms, self.draw_graphs)
        self.animate()
        self.canvas.restore_region(self.graph_area)
        self.frame_count = self.frame_count + 1
        if self.frame_count == self.frames_to_skip or self.frames_to_skip == 0:
            self.frame_count = 0
            update_axes = True
        else:
            update_axes = False
        for i in range(4):
            # plt.draw()
            # self.canvas.draw()
            self.plots[i].axes.draw_artist(self.plots[i])
            if update_axes:
                self.plots[i].axes.draw_artist(self.axes_list[i].get_xaxis())
                self.plots[i].axes.draw_artist(self.axes_list[i].get_yaxis())
            else:
                self.canvas.blit(self.plots[i].axes.bbox)
        if update_axes:
            self.canvas.blit(self.plots[0].axes.clipbox)

    def update_graphs(self):
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

            # print(time_now)
            # if time_now - self.last_update[i] > self.refresh_rate:
            self.axes_list[i].relim()
            self.axes_list[i].set_ylim(auto=True)  # In case ylim was set to a lower value for a different sensor

            if self.set_limits.get() and max(y_data) > data_limits[graph_selection]:
                self.axes_list[i].set_ylim(ymax=data_limits[graph_selection])

            self.axes_list[i].autoscale_view()
            # self.last_update[i] = time_now

            # We have to do this even if we don't change graphs because the labels get erased after we scale the axes
            self.axes_list[i].set_title(graph_selection)
            self.axes_list[i].set_xlabel(labels[graph_selection][0])
            self.axes_list[i].set_ylabel(labels[graph_selection][1])

            self.plot_selections[i] = graph_selection
        return self.plots[1], self.plots[2], self.plots[3], self.plots[0],

    # def on_closing(self):
    #     if messagebox.askokcancel("Quit", "Do you want to quit?"):
    #         self.root.destroy()
        #    self.root.quit()

    def update_log_displays(self):
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
        self.network_logs.insert('end', network_log_msg + '\n')

    def start(self):
        self.root.mainloop()
        # self.root.after(0, self.draw_graphs())
