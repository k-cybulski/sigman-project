from sigman import analyzer 
import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'parameter'
description = """Procedure calculating the heart rate based on the 
frequency of recurrence of points of a given type."""
author = 'kcybulski'
arguments = {}
default_arguments = {}
output_type = 'hr'
required_waves = []
required_points = ['r']

def procedure(waves, points, begin_time, end_time, arguments):
    r_x, r_y = points['r'].data_slice(begin_time, end_time)
    periods = np.diff(r_x)
    average_period = np.average(periods)
    heart_rate = 1/average_period
    return heart_rate * 60

def execute(waves, points, begin_time, end_time, arguments):
    return procedure(waves, points, begin_time, end_time, arguments)

