
import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = ("""Procedure search for corupted fragment of signal.
Mark physiocal occurence in cardiac cycles.
""")
author = 'mzylinski'
arguments = {
    }
default_arguments = {
    }
output_type = 'artifactBP'
required_waves = ['BP']
required_points = ['StartofCycle']



def mean(data):
    sum = 0
    if (len(data)> 0):
        for i in range(0,len(data)):
            sum = sum + data[i]

        return sum / len(data)
    else:
        return 0

def procedure(waves, points, begin_time, end_time, settings):
    wave = waves['BP']
    start = points['StartofCycle']

    r_x = []
    r_y = []

    for i in range(0,len(start) - 1):
        if (start.data_x[i]>begin_time and start.data_x[i + 1] < end_time):
            data = wave.data_slice(start.data_x[i], start.data_x[i + 1])
            
            problems = 0
            step = 50
            for j in range (0,len(data) - step):
                if (np.power((data[j] - data[j+step]),2) < 0.5):
                    problems = problems + 1
            if (problems<(len(data)*0.25)):
                r_y.append(1)
            else:
                r_y.append(0)
            r_x.append(start.data_x[i])

    return r_x, r_y

def interpret_arguments(waves, points, arguments):
    output_arguments = {}
    for key, item in arguments.items():
        try:
            output_arguments[key] = float(item)
        except:
            raise InvalidArgumentError("{} is invalid.".format(arguments[key]))
    return output_arguments

def execute(waves, points, begin_time, end_time, arguments):
    arguments = interpret_arguments(waves, points, arguments)
    return procedure(waves, points, begin_time, end_time, arguments)