from server_info import ServerInfo

labels = {
    "LC1S": ("Time(s)", "Force (N)"),
    "LC_MAIN": ("Time(s)", "Force (N)"),
    "LC2S": ("Time(s)", "Force (N)"),
    "LC3S": ("Time(s)", "Force (N)"),
    "PT_FEED": ("Time(s)", "Pressure (PSI)"),
    "PT_COMB": ("Time(s)", "Pressure (PSI)"),
    "PT_INJE": ("Time(s)", "Pressure (PSI)"),
    "TC1S": ("Time(s)", "Temperature (C)"),
    "TC2S":("Time(s)", "Temperature (C)"),
    "TC3S": ("Time(s)", "Temperature (C)"),
}

str_to_byte = {
    'LC1S': ServerInfo.LC1,
    'LC_MAIN': ServerInfo.LC_MAIN,
    'LC2S': ServerInfo.LC2,
    'LC3S': ServerInfo.LC3,
    'PT_FEED': ServerInfo.PT_FEED,
    'PT_COMB': ServerInfo.PT_COMB,
    'PT_INJE': ServerInfo.PT_INJE,
    'TC1S': ServerInfo.TC1,
    'TC2S': ServerInfo.TC2,
    'TC3S': ServerInfo.TC3
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
    "TC1": 10,
    "TC2": 10,
    "TC3": 10,
}

# Samples to keep is how many samples we actually want to show in the graph
# See data_ratio in animate() in gui_final
samples_to_keep = {
    "LC1": 500,
    "LC_MAIN": 500,
    "LC2": 500,
    "LC3": 500,
    "PT_FEED": 250,
    "PT_COMB": 250,
    "PT_INJE": 250,
    "TC1": 10,
    "TC2": 10,
    "TC3": 10,
}
