#!/usr/bin/env python3
# This script tests functions & methods of the `sigman` library
# it can be run by simply using `pytest` in the `sigman-project` directory

import sys
import os
_script_path = os.path.abspath(__file__)
_script_directory = os.path.dirname(_script_path)
_sigman_root_directory = os.path.dirname(_script_directory)
os.chdir(_script_directory)
sys.path.append(_sigman_root_directory)
import pytest

from math import isclose

import numpy as np

import sigman as sm
from sigman import file_manager as fm
from sigman import analyzer
from sigman import visualizer as vis

@pytest.fixture
def bp_wave():
    return fm.import_wave('example_data/BP.dat', 'bp')

@pytest.fixture
def sine_wave():
    sine = np.sin(np.linspace(0, 2*np.pi, num=101))
    sample_rate = 100/2.
    return sm.Wave(sine, sample_rate, 'sine')

@pytest.fixture
def simple_values():
    return [0, 1, 0, -1]

@pytest.fixture
def simple_wave(simple_values):
    return sm.Wave(simple_values, 2, 'simple')

@pytest.fixture
def r_points():
    return fm.import_points('example_data/R.dat', 'r')

@pytest.fixture
def butterworth():
    return analyzer.import_procedure("modify_filter_butterworth")

### Wave operations ###

def test_import_wave_dat():
    bp_wave = fm.import_wave('example_data/BP.dat', 'bp')
    assert round(bp_wave.value_at(2)*100)/100 == 135.04

def test_wave_offset(bp_wave):
    bp_wave.offset = -2
    assert round(bp_wave.value_at(0)*100)/100 == 135.04

def test_wave_copy(bp_wave):
    t_wave = bp_wave.copy()
    assert t_wave.type == bp_wave.type
    assert t_wave.value_at(5) == bp_wave.value_at(5)

def test_wave_sample_at(bp_wave):
    assert bp_wave.sample_at(0) == 0
    assert bp_wave.sample_at(bp_wave.complete_length) == len(bp_wave) - 1
    assert bp_wave.sample_at(200) == int(200*bp_wave.sample_rate)

def test_value_at(bp_wave, sine_wave):
    assert bp_wave.value_at(bp_wave.complete_length) == bp_wave[-1]
    assert bp_wave.value_at(0) == bp_wave[0]
    assert bp_wave.value_at(bp_wave.sample_length*200) == bp_wave[200]
    assert isclose(sine_wave.value_at(1), 0, abs_tol=0.001)

def test_import_points_dat():
    r_points = fm.import_points('example_data/R.dat', 'r')
    assert r_points[2][0] == 2.4950000000000001

def test_points_offset(r_points):
    r_points.offset(-2)
    assert r_points[2][0] == 0.4950000000000001

def test_composite_data_management(bp_wave, r_points):
    composite_data = sm.Composite_data(
        waves={
            'bp':bp_wave},
        points={
            'r':r_points})
    composite_data.delete_wave('bp')
    composite_data.add_wave(bp_wave, 'bp')
    with pytest.raises(ValueError):
        composite_data.add_wave(bp_wave, 'bp')
    composite_data.add_wave(bp_wave, 'bp', replace=True)
    composite_data.delete_points('r')
    composite_data.add_points(r_points, 'r')
    with pytest.raises(ValueError):
        composite_data.add_points(r_points, 'r')
    slice_ = composite_data.points['r'].data_slice(20, 30)
    slice_points = sm.Points(slice_[0], slice_[1], 'r')
    assert slice_points[0][0] == 20.618680000000001
    assert composite_data.points['r'][22][0] == 20.618680000000001
    composite_data.points['r'].delete_slice(20, 30)
    assert composite_data.points['r'][22][0] != 20.618680000000001
    composite_data.add_points(slice_points, 'r', join=True)
    assert composite_data.points['r'][22][0] == 20.618680000000001

def test_procedure_import():
    butterworth = analyzer.import_procedure("modify_filter_butterworth")
    assert butterworth.author == 'kcybulski'

### FIXME: Should be changed after issue #20
def test_deprecated_modify_procedure(bp_wave, butterworth):
    arguments = butterworth.default_arguments
    arguments['N'] = 3
    arguments['Wn'] = 30
    filtered_wave = analyzer.modify_wave(bp_wave, 60, 70, butterworth,
                                         arguments)
    assert isclose(filtered_wave.value_at(5), 90.11, rel_tol=0.001)
    assert filtered_wave.complete_length == 10
    assert bp_wave.value_at(65) == 89.90841097350858
    bp_wave.replace_slice(60, 70, filtered_wave)
    assert isclose(bp_wave.value_at(65), 90.11, rel_tol=0.001)

def test_wave_value_exactness(simple_values, simple_wave):
    for true, assumed in zip(simple_values, 
            simple_wave.data_slice(0, simple_wave.complete_length)):
        assert true == assumed
    for true, assumed in zip(simple_values[0:2],
                             simple_wave.data_slice(0, 1.5)):
        assert true == assumed
    for true, assumed in zip(simple_values[0:2],
                             simple_wave.data_slice(0, 1.75)):
        assert true == assumed
    assert 0.5 == simple_wave.value_at(0.25)
    assert -0.5 == simple_wave.value_at(1.25)
