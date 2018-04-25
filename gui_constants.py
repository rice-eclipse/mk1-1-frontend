from server_info import ServerInfo

labels = {
    "LC1": ("Time(s)", "Force (N)"),
    "LC_MAIN": ("Time(s)", "Force (N)"),
    "LC2": ("Time(s)", "Force (N)"),
    "LC3": ("Time(s)", "Force (N)"),
    "PT_FEED": ("Time(s)", "Pressure (PSI)"),
    "PT_COMB": ("Time(s)", "Pressure (PSI)"),
    "PT_INJE": ("Time(s)", "Pressure (PSI)"),
    "TC1": ("Time(s)", "Temperature (C)"),
    "TC2":("Time(s)", "Temperature (C)"),
    "TC3": ("Time(s)", "Temperature (C)"),
}

data_limits = {
    "LC1": 10,
    "LC_MAIN": 50,
    "LC2": 10,
    "LC3": 10,
    "PT_FEED": 900,
    "PT_COMB": 600,
    "PT_INJE": 500,
    "TC1": 50,
    "TC2": 50,
    "TC3": 50,
}

str_to_byte = {
    'LC1': ServerInfo.LC1_SEND,
    'LC_MAIN': ServerInfo.LC_MAIN_SEND,
    'LC2': ServerInfo.LC2_SEND,
    'LC3': ServerInfo.LC3_SEND,
    'PT_FEED': ServerInfo.PT_FEED_SEND,
    'PT_COMB': ServerInfo.PT_COMB_SEND,
    'PT_INJE': ServerInfo.PT_INJE_SEND,
    'TC1': ServerInfo.TC1_SEND,
    'TC2': ServerInfo.TC2_SEND,
    'TC3': ServerInfo.TC3_SEND
}

# Data lengths is how many total samples we want to keep for graphing
# e.g. 60000 at 1000 samples/second would be 1 minute of data
data_lengths = {
    "LC1": 1000,
    "LC_MAIN": 1000,
    "LC2": 1000,
    "LC3": 1000,
    "PT_FEED": 500,
    "PT_COMB": 500,
    "PT_INJE": 500,
    "TC1": 50,
    "TC2": 50,
    "TC3": 50,
}

# Samples to keep is how many samples we actually want to show in the graph
# See data_ratio in animate() in gui_final
samples_to_keep = {
    "LC1": 200,
    "LC_MAIN": 500,
    "LC2": 200,
    "LC3": 200,
    "PT_FEED": 100,
    "PT_COMB": 100,
    "PT_INJE": 100,
    "TC1": 25,
    "TC2": 25,
    "TC3": 25,
}
