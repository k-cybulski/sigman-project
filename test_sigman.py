#!/usr/bin/env python3
# This script tests functions & methods of the `sigman` library
# it can be run by simply using `pytest` in the `sigman-project` directory

import os
import pytest

import sigman as sm
from sigman import file_manager as fm
from sigman import analyzer
from sigman import visualizer as vis

os.path.dirname(os.path.abspath(__file__))

@pytest.fixture
def bp_wave():
    return fm.import_wave('example_data/BP.dat', 'bp')

@pytest.fixture
def r_points():
    return fm.import_points('example_data/R.dat', 'r')

@pytest.fixture
def butterworth():
    return analyzer.import_procedure("modify_filter_butterworth")

def test_import_wave_dat():
    bp_wave = fm.import_wave('example_data/BP.dat', 'bp')
    assert bp_wave.value_at(2) == 134.75

def test_import_points_dat():
    r_points = fm.import_points('example_data/R.dat', 'r')
    assert r_points[2][0] == 2.4950000000000001

def test_wave_offset(bp_wave):
    bp_wave.offset = -2
    assert bp_wave.value_at(0) == 134.75

def test_points_offset(r_points):
    r_points.offset(-2)
    assert r_points[2][0] == 0.4950000000000001

def test_procedure_import():
    butterworth = analyzer.import_procedure("modify_filter_butterworth")
    assert butterworth.author == 'kcybulski'

def test_deprecated_modify_procedure(bp_wave, butterworth):
    arguments = butterworth.default_arguments
    arguments['N'] = 3
    arguments['Wn'] = 30
    filtered_wave = analyzer.modify_wave(bp_wave, 60, 70, butterworth,
                                         arguments)
    assert 90.118839599334365 == filtered_wave.value_at(5)

def test_modify_procedure(bp_wave, butterworth):
    filtered_wave = analyzer.modify_wave(bp_wave, 60, 70, butterworth, 
                                         N=3, Wn=30)
    print(filtered_wave.value_at(5))
