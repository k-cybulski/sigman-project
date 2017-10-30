from sigman import analyzer 
import numpy as np
import pickle
procedure_type = 'points'
description = """Procedura przeszukująca wykresy BP i EKG za pomocą 
wytrenowanej sieci neuronowej w celu odnalezienia wcięć dykrotycznych. 
Wykorzystuje punkty SBP do zawężenia poszukiwania.

Opcjonalne argumenty:
['net_file']:'procedures/default_dn_net.pickle': string; ścieżka i 
             nazwa pliku sieci neuronowej
['focus_range']:(0.01,0.05): tuple (float, float); zakres czasowy z 
                którym po punktach SBP szukane będą DN
['test_every']:0.005: float; co ile sekund ma być testowany każdy punkt
                w focus_range
"""
author = 'kcybulski'
required_lines = ['bp','ecg']
required_points = ['sbp']
default_settings = {'net_file':'procedures/default_dn_net.pickle', 'focus_range':(0.1,0.5), 'test_every':0.005}
required_arguments = []

# Poniższa klasa zostanie usunięta w przyszłości
# Na razie służy tylko do tego by umożliwic korzystanie z .pickle na pre-uczonych sieciach neuronowych
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

def procedure(comp_data, begin_time, end_time, settings):
    ecg_line = comp_data.data_lines['ecg']
    bp_line = comp_data.data_lines['bp']
    sbp_points = comp_data.data_points['sbp']
    focus_range = settings['focus_range']
    test_every = settings['test_every']

    # Importujemy sieć neuronową
    net = pickle.load(open(settings['net_file'],'rb'))
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
