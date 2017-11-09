from sigman import analyzer 
import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'parameter'
description = """Procedura obliczająca częstotliwość bicia serca na 
minutę w oparciu o punkty R.
"""
author = 'kcybulski'
arguments = {}
default_arguments = {}
required_waves = []
required_points = ['r']

def validate_arguments(composite_data, arguments):
    return True, "" # nie ma argumentów

def procedure(comp_data, begin_time, end_time, arguments):
    r_x, r_y = comp_data.data_points['r'].data_slice(begin_time, end_time)
    periods = np.diff(r_x)
    average_period = np.average(periods)
    heart_rate = 1/average_period
    return heart_rate * 60

def execute(comp_data, begin_time, end_time, arguments):
    return procedure(comp_data, begin_time, end_time, arguments)

