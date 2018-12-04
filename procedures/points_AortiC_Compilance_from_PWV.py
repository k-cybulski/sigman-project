import numpy as np
import math as m
from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure calculate arterial compilance from PWV use Maens-Kortweg equation
""")
author = 'mzylinski'
arguments = {
     'age':"How old are patient?",
     'height':"How many meter patient have?",
     'mass':"How much he weighed?"
    
    }
default_arguments = {
    'age':'35',
    'height':'1.75',
    'mass':'75'
    }
output_type = 'C_PWV'
required_waves = []
required_points = ['PWV']


def calculate_BSA (height,mass):
    bsa = 0.20247*m.pow(height,0.725)*m.pow(mass,0.425)
    return bsa

def calculate_Q0 (BSA, age):
    q0 = m.pow(age,(0.3888*m.pow(BSA,0.5)))
    return q0

def calculate_VW (Q0, height):
    lw = height*0.3
    vw= Q0*lw
    return vw

def procedure(waves, points, begin_time, end_time, settings):
    PWV = points['PWV']

    P_age =  float(settings['age'])
    P_height = float(settings['height'])
    P_mass = float(settings['mass'])
    
    P_BSA = calculate_BSA(P_height,P_mass)
    P_Q0 = calculate_Q0 (P_BSA,P_age)
    P_VW = calculate_VW (P_Q0,P_height)

    blood_denisty = 1.054

    r_x = []
    r_y = []
  
    for i in range(0,len(PWV)):
        
        C = P_VW / (PWV.data_y[i]*PWV.data_y[i]*blood_denisty)

        r_x.append(PWV.data_x[i])
        r_y.append(C)


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