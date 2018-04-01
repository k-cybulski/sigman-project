from sigman import analyzer 
import numpy as np
import pickle

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""
Procedure searching for dicrotic notches based on BP and ECG signals
by using a trained neural network.

It also makes use of SBP points to narrow the searching area.
""")
author = 'kcybulski'
arguments = {
    'net':"Path to the pickled neural network file",
    'focus_range':("Time range from an SBP point in which DNs are searched "
                   "for; two numbers separated by a comma."),
    'test_every':("Distance between points tested within focus_range. "
                  "The less the more accurate.")}
default_arguments = {'net':'procedures/default_dn_net.pickle',
                     'focus_range':'0.1,0.5', 'test_every':0.005}
output_type = 'dn'
required_waves = ['bp','ecg']
required_points = ['sbp']

class Temp_Network():
    def __init__(self,network):
        self.input_point_count = network.shape[0]
        self.sample_length = network.sample_length
        self.detection_point_offset = network.detection_point
        self.w = network.w
        self.b = network.b
        self.activation = np.tanh
    def forward(self, x):
        a = x
        for i in range(len(self.w)):
            z = a.dot(self.w[i])+self.b[i]
            a = self.activation(z)
        return a

def interpret_arguments(waves, points, arguments):
    # net
    try:
        net = pickle.load(open(arguments['net'], 'rb'))
    except:
        raise InvalidArgumentError("Invalid neural net file")
    # focus_range
    try:
        focus_range = [float(string) for string in
                       arguments['focus_range'].split(',')]
    except:
        raise InvalidArgumentError("Invalid focus range")
    if len(focus_range) != 2:
        raise InvalidArgumentError("Invalid number of focus range values")
    try:
        test_every = float(arguments['test_every'])
    except:
        raise InvalidArgumentError("Invalid `test_every` value")
    return {
        'net':net,
        'focus_range':focus_range,
        'test_every':test_every}

def _generate_input_data_sample(bp_line, ecg_line, test_point, sample_length, 
                               detection_point_offset, input_point_count):
    """Generates a single set of input data to analyse with the neural net."""
    begin_time = test_point - detection_point_offset
    end_time = begin_time + sample_length
    bp_data = bp_line.data_slice(begin_time, end_time, 
                                 value_count = int(input_point_count/2))
    ecg_data = ecg_line.data_slice(begin_time, end_time, 
                                   value_count = int(input_point_count/2))
    # Normalisation
    bp_data-=np.min(bp_data)
    bp_data/=np.max(bp_data)
    bp_data*=2
    bp_data-=1
    ecg_data-=np.min(ecg_data)
    ecg_data/=np.max(ecg_data)
    ecg_data*=2
    ecg_data-=1
    input_data = np.concatenate((bp_data,ecg_data))
    return input_data

def procedure(waves, points, begin_time, end_time, arguments):
    ecg_line = waves['ecg']
    bp_line = waves['bp']
    sbp_points = points['sbp']
    focus_range = arguments['focus_range']
    test_every = arguments['test_every']
    net = arguments['net']

    sample_length = net.sample_length
    detection_point_offset = net.detection_point_offset
    input_point_count = net.input_point_count
    
    sbp_x, sbp_y = sbp_points.data_slice(begin_time, end_time, left_offset = 1)
    dn_x = []
    dn_y = []
    for helper_x in sbp_x:
        if helper_x + focus_range[0] - sample_length < begin_time:
            continue
        if helper_x + focus_range[1] - detection_point_offset + sample_length > end_time:
            break
        focus_begin_time = helper_x + focus_range[0]
        focus_end_time = helper_x + focus_range[1]
        max_val = -1
        max_x = 0
        for test_x in np.arange(focus_begin_time, focus_end_time, test_every):
            input_data = _generate_input_data_sample(
                bp_line, ecg_line, test_x, 
                sample_length, detection_point_offset, 
                input_point_count)
            val = net.forward(input_data)[0][0]
            if val > max_val:
                max_val = val
                max_x = test_x
        dn_x.append(max_x)
        dn_y.append(bp_line.value_at(max_x))
    dn_x = np.array(dn_x)
    dn_y = np.array(dn_y)
    return dn_x, dn_y

def execute(waves, points, begin_time, end_time, arguments):
    arguments = interpret_arguments(waves, points, arguments)
    return procedure(waves, points, begin_time, end_time, arguments)
