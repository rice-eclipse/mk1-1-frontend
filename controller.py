"""
This file defines GUIController, which instantiates a GUIBackend
and GUIFrontend instance, and the adapters between them. Run this
file to start mission control.
"""

import configparser

from model import GUIBackend
from view import GUIFrontend


class GUIController:
    """
    The GUIController knows about both GUIFrontend and GUIBackend. It
    instantiates each and sets up their adapters so they can communicate
    without breaking decoupling.
    """

    def __init__(self):
        config = configparser.RawConfigParser()
        config.read('config.ini')

        class Back2FrontAdapter:
            """
            An adapter from GUIBackend to GUIFrontend, which allows
            the backend to call methods on the frontend without depending
            on implementation details in the frontend.
            """

            def __init__(self):
                nonlocal frontend

            @staticmethod
            def display_msg(msg):
                """
                Displays a text message in the GUI.
                @param msg: The message to display.
                """
                frontend.network_log_append(msg)

        class Front2BackAdapter:
            """
            An adapter from GUIFrontend to GUIBackend, which allows
            the frontend to call methods on the backend without depending
            on implementation details in the backend.
            """

            def __init__(self):
                nonlocal backend

            @staticmethod
            def connect(ip, port):
                """
                Connect to a given port at a given address.
                @param ip: The IP address to connect to.
                @param port: The port.
                """
                backend.connect(ip, port)

            @staticmethod
            def disconnect():
                """
                Disconnect from the server if we are currently connected.
                """
                backend.disconnect()

            @staticmethod
            def send(b):
                """
                Send a byte across the network.
                @param b: The byte to send.
                """
                backend.send(b)

            @staticmethod
            def get_all_queues():
                """
                Get all data queues.
                @return: A list containing data queues that store sensor data.
                """
                return backend.get_all_queues()

            @staticmethod
            def get_queue(name):
                """
                Get a particular queue by name, e.g. "LC1"
                @param name: The name of the desired queue.
                @return: The queue corresponding to the given name.
                """
                return backend.get_queue(name)

            @staticmethod
            def add_point(p):
                """
                Adds a calibration data point for the backend
                to process.
                @param p: A (raw_value, expected_value) ordered pair.
                """
                backend.add_point(p)

            @staticmethod
            def clear_calibration():
                """
                Removes any stored calibration points from the backend.
                """
                backend.clear_calibration()

            @staticmethod
            def get_calibration():
                """
                Calculates the slope and y-intercept of the stored data.
                Assumes the calibration curve is linear.
                """
                return backend.get_calibration()

        backend = GUIBackend(Back2FrontAdapter(), config)
        self.backend = backend

        frontend = GUIFrontend(Front2BackAdapter(), config)
        self.frontend = frontend

    def start(self):
        """
        Starts the controller by starting the backend and the
        frontend.
        """
        self.backend.start()
        self.frontend.start()


def main():
    """
    Starts mission control by instantiating and starting GUIController.
    """
    controller = GUIController()
    controller.start()


if __name__ == "__main__":
    main()
