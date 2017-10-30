"""
W tym pliku definiowane są proste funkcje służące do szybkiego wizualizowania
danych.
"""


from matplotlib import pyplot as plt

import sigman


# Kolory różnych rodzajów danych
type_colors={'ecg':'C0', 'bp':'C1', 
             'r':'r', 
             'sbp':'#886600', 'dbp':'#AA9900', 'dn':'y'}


def visualize_composite_data(comp_data, begin_time=None, end_time=None, 
    title="", wanted_lines=None, wanted_points=None):
    """Szybka i nieestetyczna funkcja do wizualizacji danych zawartych
    w Composite_data.
    """
    # Ustalamy zakres czasu, który chcemy pokazać
    # jeśli wanted_lines są ustawione, to ograniczymy zakres tylko do nich
    # jeśli nie są, to pokażemy wszystkie dane które mamy
    if end_time is None or begin_time is None:
        if wanted_lines is not None:
            temp_begin_time, temp_end_time = comp_data.calculate_time_range(
                required_lines = wanted_lines)
        else:
            temp_begin_time, temp_end_time = comp_data.calculate_complete_time_span()
        if begin_time is None:
            begin_time = temp_begin_time
        if end_time is None:
            end_time = temp_end_time
    if wanted_lines is None:
        for key, data_line in comp_data.data_lines.items():
            temp_begin_time = max(begin_time, data_line.offset)
            temp_end_time = min(end_time, data_line.offset 
                                + data_line.complete_length)
            x, y = data_line.generate_coordinate_tables(
                begin_time = temp_begin_time, 
                end_time = temp_end_time, 
                begin_x = temp_begin_time)
            if data_line.line_type in type_colors:
                color = type_colors[data_line.line_type]
            else:
                color = None
            plt.plot(x, y, color = color, 
                label = data_line.line_type)
    else:
        for dict_type in wanted_lines:
            data_line = comp_data.data_lines[dict_type]
            x, y = data_line.generate_coordinate_tables(
                begin_time = begin_time, 
                end_time = end_time, 
                begin_x = begin_time)
            if data_line.line_type in type_colors:
                color = type_colors[data_line.line_type]
            else:
                color = None
            plt.plot(x, y, color = color, 
                label = data_line.line_type)
    if wanted_points is None:
        for key, data_points in comp_data.data_points.items():
            x, y = data_points.data_slice(begin_time, end_time)
            if data_points.point_type in type_colors:
                color = type_colors[data_points.point_type]
            else:
                color = none
            plt.plot(x, y, color = color, 
                label = data_points.point_type, 
                marker='o', linestyle='None')
    else:
        for dict_type in wanted_points:
            data_points = comp_data.data_points[dict_type]
            x, y = data_points.data_slice(begin_time, end_time)
            if data_points.point_type in type_colors:
                color = type_colors[data_points.point_type]
            else:
                color = none
            plt.plot(x, y, color = color, 
            label = data_points.point_type, 
            marker='o', linestyle='None')
    plt.suptitle(title)
    plt.show()

