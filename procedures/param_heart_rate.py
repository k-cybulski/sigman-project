from sigman import analyzer 
import numpy as np
procedure_type = 'param'
description = """Procedura obliczająca częstotliwość bicia serca na 
minutę w oparciu o punkty R.
"""
author = 'kcybulski'
required_lines = []
required_points = ['r']
default_settings = {}
required_arguments = []
def procedure(comp_data, begin_time, end_time, settings):
    r_x, r_y = comp_data.data_points['r'].data_slice(begin_time, end_time)
    periods = np.diff(r_x)
    average_period = np.average(periods)
    heart_rate = 1/average_period
    return heart_rate * 60
