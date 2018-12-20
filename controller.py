import configparser

from model import GUIBackend
from view import GUIFrontend

config = configparser.RawConfigParser()
config.read('config.ini')

backend = GUIBackend(config)
frontend = GUIFrontend(backend, config)
frontend.root.mainloop()
