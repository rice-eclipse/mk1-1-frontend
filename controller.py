import configparser

from model import GUIBackend
from view import GUIFrontend


class GUIController:
    def __init__(self):
        config = configparser.RawConfigParser()
        config.read('config.ini')

        self.backend = GUIBackend(config)
        self.frontend = GUIFrontend(self.backend, config)

    def start(self):
        self.backend.start()
        self.frontend.start()


def main():
    controller = GUIController()
    controller.start()


if __name__ == "__main__":
    main()
