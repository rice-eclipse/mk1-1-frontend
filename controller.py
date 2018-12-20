import configparser

from model import GUIBackend
from view import GUIFrontend


class GUIController:
    def __init__(self):
        config = configparser.RawConfigParser()
        config.read('config.ini')

        class front2back_adapter:
            def __init__(self):
                nonlocal backend

            def connect(self, ip, port):
                backend.connect(ip, port)

            def disconnect(self):
                backend.disconnect()

            def send(self, b):
                backend.send(b)

            def get_all_queues(self):
               return backend.get_all_queues()

            def get_queue(self, name):
                return backend.get_queue(name)

        backend = GUIBackend(config)
        self.backend = backend

        frontend = GUIFrontend(front2back_adapter(), config)
        self.frontend = frontend

    def start(self):
        self.backend.start()
        self.frontend.start()


def main():
    controller = GUIController()
    controller.start()


if __name__ == "__main__":
    main()
