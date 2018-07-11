#!/usr/bin/env python3
# This script tests if a simple analysis can be performed and not crash

import sys
import os
_script_path = os.path.abspath(__file__)
_script_directory = os.path.dirname(_script_path)
_sigman_root_directory = os.path.dirname(_script_directory)
os.chdir(_script_directory)
sys.path.append(_sigman_root_directory)
import pytest

from sigman import file_manager as fm
from sigman import analyzer

@pytest.fixture
def messy_ecg_wave():
    return fm.import_wave('example_data/ECG_messy.dat', 'ecg')

@pytest.fixture
def filter_procedure():
    butterworth = analyzer.import_procedure("modify_filter_butterworth")
    arguments = butterworth.default_arguments
    arguments['N'] = 3
    arguments['Wn'] = 30
    return lambda wave, start, end: analyzer.modify_wave(wave, start, end,
                                                         butterworth,
                                                         arguments)

@pytest.fixture
def r_points_procedure():
    find_r = analyzer.import_procedure('points_r_simple')
    arguments = find_r.default_arguments
    return lambda wave, start, end: analyzer.find_points({'ecg':wave}, [], start, end,
                                                         find_r,
                                                         arguments)

@pytest.fixture
def hr_procedure():
    calculate_hr = analyzer.import_procedure('parameter_heart_rate')
    return lambda points, start, end: analyzer.calculate_parameter(
        [], {'r':points}, 
        [(start, end)],
        calculate_hr,
        {})

def test_filter(messy_ecg_wave, filter_procedure):
    filtered_wave = filter_procedure(messy_ecg_wave, 0, 30)
    messy_ecg_wave.replace_slice(0, 30, filtered_wave)

def test_full_analysis(messy_ecg_wave, filter_procedure, r_points_procedure,
                       hr_procedure):
    filtered_wave = filter_procedure(messy_ecg_wave, 0,
                                     messy_ecg_wave.complete_length)
    points = r_points_procedure(filtered_wave, 0, filtered_wave.complete_length)
    heart_rate = hr_procedure(points, 0, filtered_wave.complete_length)
    print(heart_rate.values[0])
    assert heart_rate.values[0] > 50 and heart_rate.values[0] < 200
