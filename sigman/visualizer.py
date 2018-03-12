"""
W tym pliku definiowane są proste funkcje służące do szybkiego wizualizowania
danych.
"""
from matplotlib import pyplot as plt

import sigman as sm

# Kolory różnych rodzajów danych
type_colors={'ecg':'C0', 'bp':'C1', 
             'r':'r', 
             'sbp':'#886600', 'dbp':'#AA9900', 'dn':'y',
             'hr':'C2'}

def show(obj, **kwargs):
    if isinstance(obj, sm.Composite_data):
        show_composite_data(obj, **kwargs)
    elif isinstance(obj, sm.Wave):
        show_wave(obj, **kwargs)
    elif isinstance(obj, sm.Points):
        show_points(obj, **kwargs)

def _plot_wave(wave, begin_time, end_time, **kwargs):
    x, y = wave.generate_coordinate_tables(
        begin_time = begin_time, 
        end_time = end_time, 
        begin_x = begin_time)
    if kwargs.get('color') is None:
        if wave.type in type_colors:
            kwargs['color'] = type_colors[wave.type]
        else:
            kwargs['color'] = None
    if kwargs.get('label') is None:
        kwargs['label'] = wave.type
    plt.plot(x, y, **kwargs)

def show_wave(wave, begin_time=None, end_time=None, **kwargs):
    if begin_time is None:
        begin_time = wave.offset
    if end_time is None:
        end_time = wave.complete_length - wave.offset
    _plot_wave(wave, begin_time, end_time, **kwargs)
    plt.show()

def _plot_points(points, begin_time, end_time, **kwargs):
        x, y = points.data_slice(begin_time, end_time)
        if kwargs.get('color') is None:
            if points.type in type_colors:
                color = type_colors[points.type]
            else:
                color = None
        if kwargs.get('label') is None:
            kwargs['label'] = points.type
        if kwargs.get('marker') is None:
            kwargs['marker'] = 'o'
        if kwargs.get('linestyle') is None:
            kwargs['linestyle'] = 'None'
        plt.plot(x, y, **kwargs)

def show_points(points, begin_time=None, end_time=None, **kwargs):
    if begin_time is None:
        begin_time = points[0][0]
    if end_time is None:
        end_time = points[-1][0]
    _plot_points(points, begin_time, end_time, **kwargs)
    plt.show()

def show_composite_data(comp_data, begin_time=None, end_time=None, 
    title="", wanted_waves=None, wanted_points=None, wanted_parameters=None):
    """Szybka i nieestetyczna funkcja do wizualizacji danych zawartych
    w Composite_data. Pokazuje okno matplotlib uwzględniające wszystkie
    wymagane przebiegi i punkty.
    """
    # Ustalamy zakres czasu, który chcemy pokazać
    # jeśli wanted_waves są ustawione, to ograniczymy zakres tylko do nich
    # jeśli nie są, to pokażemy wszystkie dane które mamy
    if end_time is None or begin_time is None:
        if wanted_waves is not None:
            temp_begin_time, temp_end_time = comp_data.calculate_time_range(
                required_waves = wanted_waves)
        else:
            temp_begin_time, temp_end_time = comp_data.calculate_complete_time_span()
        if begin_time is None:
            begin_time = temp_begin_time
        if end_time is None:
            end_time = temp_end_time
    if wanted_waves is None:
        for key, wave in comp_data.waves.items():
            temp_begin_time = max(begin_time, wave.offset)
            temp_end_time = min(end_time, wave.offset 
                                + wave.complete_length)
            _plot_wave(wave, temp_begin_time, temp_end_time)
    else:
        for dict_type in wanted_waves:
            wave = comp_data.waves[dict_type]
            _plot_wave(wave, temp_begin_time, temp_end_time)
    if wanted_points is None:
        for key, points in comp_data.points.items():
            _plot_points(points, begin_time, end_time)
    else:
        for dict_type in wanted_points:
            points = comp_data.points[dict_type]
            _plot_points(points, begin_time, end_time)
    if wanted_parameters is None:
        for key, parameter in comp_data.parameters.items():
            line_tuples = parameter.generate_parameter_line_tuples(
                begin_time = begin_time, 
                end_time = end_time)
            if parameter.type in type_colors:
                color = type_colors[parameter.type]
            else:
                color = 'C2'
            for tup in line_tuples:
                plt.plot(tup[0],tup[1], color=color)
    else:
        for dict_type in wanted_parameters:
            parameter = comp_data.parameters[dict_type]
            line_tuples = parameter.generate_parameter_line_tuples(
                begin_time = begin_time, 
                end_time = end_time)
            if parameter.type in type_colors:
                color = type_colors[parameter.type]
            else:
                color = 'C2'
            for tup in line_tuples:
                plt.plot(tup[0],tup[1], color=color)
    plt.suptitle(title)
    plt.show()

