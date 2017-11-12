from sigman import analyzer 
import numpy as np
import pickle

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedura przeszukująca wykresy BP i EKG za pomocą wytrenowanej sieci
neuronowej w celu odnalezienia wcięć dykrotycznych. 

Wykorzystuje punkty SBP do zawężenia poszukiwania.
""")
author = 'kcybulski'
arguments = {
    'net':"Scieżka i nazwa pliku sieci neuronowej",
    'focus_range':("Zakres czasu od punktu SBP po którym szukany jest "
                   "DN. Zapisany w formie dwóch wartości "
                   "przedzielonych przecinkiem."),
    'test_every':"Odstęp między badanymi punktami w focus_range"}
default_arguments = {'net':'procedures/default_dn_net.pickle',
                     'focus_range':'0.1,0.5', 'test_every':0.005}
required_waves = ['bp','ecg']
required_points = ['sbp']

# Poniższa klasa zostanie usunięta w przyszłości
# Na razie służy tylko do tego by umożliwic korzystanie z pickle na pre-uczonych sieciach neuronowych
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

def validate_arguments(comp_data, arguments):
    """Sprawdza, czy podane argumenty są poprawne."""
    # net
    try:
        with open(arguments['net']) as net:
            pickle.load(net)
    except:
        return False, "Niewłaściwy plik sieci neuronowej"
    # focus_range
    try:
        vals = arguments['focus_range'].split(';')
        if len(vals) != 2:
            return False, "Niewłaściwy focus_range"
    except:
        return False, "Niewłaściwy focus_range"
    # test_every 
    try:
        float(arguments['test_every'])
    except:
        return False, "Niewłaściwy test_every"
    return True, ""

def interpret_arguments(arguments):
    net = pickle.load(open(arguments['net']).read())
    focus_range = []
    for string in arguments['focus_range'].split(','):
        focus_range.append(float(string))
    test_every = float(arguments['test_every'])
    return {
        'net':net,
        'focus_range':focus_range,
        'test_every':test_everu}

def _generate_input_data_sample(bp_line, ecg_line, test_point, sample_length, 
                               detection_point_offset, input_point_count):
    """Generuje pojedyncze dane wejsciowe z wycinka wykresu EKG i BP
    do sprawdzenia siecią neuronową.
    """
    begin_time = test_point - detection_point_offset
    end_time = begin_time + sample_length
    bp_data = bp_line.data_slice(begin_time, end_time, 
                                 value_count = int(input_point_count/2))
    ecg_data = ecg_line.data_slice(begin_time, end_time, 
                                   value_count = int(input_point_count/2))
    # Normalizujemy dane dla sieci do zakresu <-1; 1>
    bp_data-=np.min(bp_data)
    bp_data/=np.max(bp_data)
    bp_data*=2
    bp_data-=1
    ecg_data-=np.min(ecg_data)
    ecg_data/=np.max(ecg_data)
    ecg_data*=2
    ecg_data-=1
    # Łączymy wycinek BP i EKG
    input_data = np.concatenate((bp_data,ecg_data))
    return input_data

def procedure(comp_data, begin_time, end_time, arguments):
    ecg_line = comp_data.data_waves['ecg']
    bp_line = comp_data.data_waves['bp']
    sbp_points = comp_data.data_points['sbp']
    focus_range = arguments['focus_range']
    test_every = arguments['test_every']

    # Importujemy sieć neuronową
    net = pickle.load(open(arguments['net'],'rb'))
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

def execute(data_wave, begin_time, end_time, arguments):
    """Sprawdza poprawność argumentów i wykonuje procedurę."""
    valid, error_message = validate_arguments(data_wave, arguments)
    if not valid:
        raise InvalidArgumentError(error_message)
    arguments = interpret_arguments(arguments)
    return procedure(data_wave, begin_time, end_time, arguments)
