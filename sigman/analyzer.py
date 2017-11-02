"""
W tym pliku znajdują się funkcje pozwalające importować oraz stosować
zewnętrzne procedury na danych. 

Procedury znajdują się w plikach w folderze 'procedures'. 

Każdy plik procedury jest pojedynczym pythonowym modułem który powinien 
zawierać atrybuty:
    <string> procedure_type - typ procedury; mogą być "filter","points" 
                              lub "misc"
        "filter" oznacza procedurę filtrowania, która przyjmuje tylko linię 
            danych do przefiltrowania oraz zakres czasu działania i 
            dodatkowe argumenty
        "points" oznacza procedurę odnajdującą punkty, która przyjmuje
            zestaw linii danych oraz odkrytych już punktów i dodatkowe
            argumenty
        "misc" oznacza procedurę o bliżej nieokreślonym zastosowaniu,
            np. obliczającą tętno w danym zakresie czasu
    <string> description - opis celu i działania procedury
    <string> author - autor procedury
    <dict> default_settings - dict z domyślnymi argumentami procedury
    <lista string> required_arguments - wymagane argumenty procedury
    <function> procedure - procedura; opisana niżej

Procedury poza procedurą filtracji powinny zawierać jeszcze atrybuty:
    <lista string> required_lines - wymagane rodzaje danych dla procedury
    <lista string> required_points - wymagane punkty dla procedury

Zależnie od rodzaju procedury funkcja procedure powinna mieć inną
strukturę. Poniżej opisane dla każdego rodzaju procedury:
    'filter'
        procedure(<Data_line> data_line, 
                  <float> begin_time, <float> end_time,
                  <dict> settings)
        procedura powinna zwracać przefiltrowaną tablicę wartości
        sygnału
    'points'
        procedure(<Composite_data> comp_data,
                  <float> begin_time, <float> end_time,
                  <dict> settings)
        procedura zwraca dwie tablice - współrzędnych x i y punktów
    'misc'
        procedure(<Composite_data> comp_data,
                  <float> begin_time, <float> end_time,
                  <dict> settings)
        procedura nie ma wymagań do tego, co zwraca

Przykład zastosowania:
    butterworth = analyzer.import_procedure("filter_butterworth")
    settings = butterworth.default_settings
    settings['N'] = 3
    settings['Wn'] = 30
    filtered_data_line = analyzer.filter_line(complete_data.data_lines['bp'], 60, 70, butterworth, settings)
    complete_data.data_lines['bp'].replace_slice(60, 70, filtered_data_line)

"""


import importlib

import sigman as sm

def import_procedure(name):
    """Zwraca moduł procedury o danej nazwie z folderu procedures."""
    procedure = importlib.import_module("procedures."+name)
    return procedure

def filter_line(data_line, begin_time, end_time, 
                procedure, settings, 
                line_type = None):
    """Filtruje Data_line podaną procedurą filtracji."""
    if line_type is None:
        line_type = data_line.type
    if (not all(settings[setting] is not None 
               for setting in procedure.required_arguments)):
        raise ValueError('Nie wszystkie wymagane argumenty z %s'
                         'są ustalone' % procedure.required_arguments)
    filtered_data = procedure.procedure(data_line, begin_time, end_time, settings)
    return sm.Data_line(filtered_data, end_time-begin_time, 
                        line_type = line_type)
    
def find_points(composite_data, begin_time, end_time, 
                procedure, settings, 
                point_type = None):
    """Odnajduje punkty na danym zakresie czasu za pomocą podanej 
    procedury.
    """
    if (not all(settings[setting] is not None 
               for setting in procedure.required_arguments)):
        raise ValueError('Nie wszystkie wymagane argumenty z %s'
                         'są ustalone' % procedure.required_arguments)
    if not all(line in composite_data.data_lines for line in procedure.required_lines):
        raise ValueError('Composite_data nie zawiera wymaganych linii z %s'
                         % procedure.required_lines)
    if not all(points in composite_data.data_points for points in procedure.required_points): 
        raise ValueError('Composite_data nie zawiera wymaganych punktów z %s'
                         % procedure.required_points)

    found_points_x, found_points_y = procedure.procedure(
        composite_data, 
        begin_time, end_time, 
        settings)
    return sm.Data_points(found_points_x, found_points_y, 
                          point_type = point_type)

def calculate_parameter(composite_data, time_tuples,
                         procedure, settings, parameter_type):
    """Przeprowadza procedurę obliczającą parametry na danym 
    Composite_data w danych zakresach czasowych i zwraca utworzony Parameter.
    """
    if (not all(settings[setting] is not None 
               for setting in procedure.required_arguments)):
        raise ValueError('Nie wszystkie wymagane argumenty z %s'
                         'są ustalone' % procedure.required_arguments)
    if not all(line in composite_data.data_lines for line in procedure.required_lines):
        raise ValueError('Composite_data nie zawiera wymaganych linii z %s'
                         % procedure.required_lines)
    if not all(points in composite_data.data_points for points in procedure.required_points): 
        raise ValueError('Composite_data nie zawiera wymaganych punktów z %s'
                         % procedure.required_points)
    parameter = sm.Parameter(parameter_type)
    for begin_time, end_time in time_tuples:
        value = procedure.procedure(composite_data, begin_time, end_time,
                                    settings)
        parameter.add_value(begin_time, end_time, value)
    return parameter

def run_misc_procedure(composite_data, begin_time, end_time,
                       procedure, settings):
    """Przeprowadza bliżej nieokreśloną procedurę na Composite_data
    i zwraca jej wynik.
    procedury.
    """
    if (not all(settings[setting] is not None 
               for setting in procedure.required_arguments)):
        raise ValueError('Nie wszystkie wymagane argumenty z %s'
                         'są ustalone' % procedure.required_arguments)
    if not all(line in composite_data.data_lines for line in procedure.required_lines):
        raise ValueError('Composite_data nie zawiera wymaganych linii z %s'
                         % procedure.required_lines)
    if not all(points in composite_data.data_points for points in procedure.required_points): 
        raise ValueError('Composite_data nie zawiera wymaganych punktów z %s'
                         % procedure.required_points)
    return procedure.procedure(composite_data, begin_time, end_time, settings)
