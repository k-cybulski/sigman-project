"""
W tym pliku znajdują się funkcje pozwalające importować oraz stosować
zewnętrzne procedury na danych. 

Procedury znajdują się w plikach w folderze 'procedures'. Są trzy
typy procedur:
    modify - procedura modyfikująca przebieg sygnału. Dane przyjmuje w
             formie Wave.
             (przykład 'parameters/modify_filter_butterworth.py')
    points - procedura odnajdująca punkty na przebiegu sygnału.
             Dane przyjmuje w formie dict Wave i dict Points.
             (przykład 'parameters/points_dbp_simple.py')
    parameter - procedura obliczająca parametry w oparciu o punkty
                oraz przebiegi.
                (przykład 'procedures/parameter_heart_rate.py')

Procedury poza danymi przyjmują także dodatkowe argumenty w formie
dict nazw argumentów i ich wartości. Procedura powinna być w stanie
interpretować argumenty wpisane jako string.

Każdy plik procedury jest pojedynczym pythonowym modułem który powinien 
zawierać atrybuty:
    <string> procedure_type - typ procedury; mogą być "modify","points" 
                              lub "parameter"
    <string> description - opis celu i działania procedury
    <string> author - autor procedury
    <dict> arguments - dict nazw argumentów oraz objaśnień, co oznaczają
    <dict> default_arguments - dict z domyślnymi argumentami procedury
    <funkcja> validate_arguments - funkcja, która sprawdza poprawność
                                   danego dict z argumentami
    <funkcja> procedure - procedura; opisana niżej
    <funkcja> execute - funkcja wywoływana z zewnątrz, która sprawdza
                        poprawność argumentów, interpretuje je oraz
                        przeprowadza samą procedurę

Ponadto procedury poza procedurami modyfikacji powinny zawierać jeszcze:
    <string> output_type - typ danych zwracany, np. dla punktów R 'r' a dla
                           parametru częstotliwości bicia serca 'hr'
    <lista string> required_waves - wymagane rodzaje przebiegów dla procedury
    <lista string> required_points - wymagane rodzaje punktów dla procedury

Zależnie od rodzaju procedury funkcja procedure powinna mieć inną
strukturę. Poniżej opisane dla każdego rodzaju procedury:
    'modify'
        procedure(<Wave> wave, 
                  <float> begin_time, <float> end_time,
                  <dict> arguments)
        procedura powinna zwracać zmodyfikowaną tablicę wartości
        sygnału o długości danego odcinka czasowego
    'points'
        procedure(<dict> waves, <dict> points,
                  <float> begin_time, <float> end_time,
                  <dict> arguments)
        procedura zwraca dwie tablice - współrzędnych x i y punktów
    'parameter'
        procedure(<dict> waves, <dict> points,
                  <float> begin_time, <float> end_time,
                  <dict> arguments)
        procedura powinna zwracać wartość parametru na danym czasie

Przykład zastosowania:
    butterworth = analyzer.import_procedure("modify_filter_butterworth")
    arguments = butterworth.default_arguments
    arguments['N'] = 3
    arguments['Wn'] = 30
    filtered_wave = analyzer.modify_wave(composite_data.waves['bp'], 60, 70, butterworth, arguments)
    complete_data.waves['bp'].replace_slice(60, 70, filtered_wave)
"""

import importlib

import sigman as sm

class InvalidArgumentError(Exception):
    """Wywołana, gdy procedura otrzyma niepoprawny argument"""

class InvalidProcedureError(Exception):
    """Wywołana, gdy procedura nie spełnia wymagań API (określonego
    powyżej)
    """

def validate_procedure_compatibility(procedure_module):
    """Sprawdza, czy dany moduł procedury spełnia wymagania API
    przedstawione powyżej. Zwraca boolean określający czy moduł spełnia
    API, oraz wiadomość błędu jeśli nie.
    """
    #TODO: Poza sprawdzaniem samej obecności atrybutów funkcja powinna
    # też sprawdzać, czy są one odpowiedniego typu (string/lista/funkcja)
    
    if 'procedure_type' not in procedure_module.__dict__:
        return False, ('procedure_type nie został zadeklarowany w module '
                       'procedury')
    procedure_type = procedure_module.procedure_type
    if procedure_type not in ['modify', 'points', 'parameter']:
        error_message = "procedure_type "+procedure_type+" jest niewłaściwy"
        return False, error_message

    required_attributes = [
        "description",
        "author",
        "arguments",
        "default_arguments",
        "validate_arguments",
        "procedure",
        "execute"]
    if procedure_type in ['points', 'parameter']:
        required_attributes.extend([
            "required_waves",
            "required_points",
            "output_type"])
    
    for attribute in required_attributes:
        if attribute not in procedure_module.__dict__:
            error_message = "atrybut "+attribute+(" nie został "
                "zadeklarowany w module procedury")
            return False, error_message
    return True, ""
    
def import_procedure(name):
    """Zwraca moduł procedury o danej nazwie z folderu procedures."""
    procedure = importlib.import_module("procedures."+name)
    valid, error_message = validate_procedure_compatibility(procedure)
    if not valid:
        raise InvalidProcedureError(error_message)
    return procedure

def modify_wave(wave, begin_time, end_time, 
                procedure, arguments, 
                wave_type=None):
    """Filtruje Wave podaną procedurą filtracji."""
    if wave_type is None:
        wave_type = wave.type
    modified_data = procedure.execute(wave, begin_time, end_time, arguments)
    return sm.Wave(modified_data, 
                   len(modified_data)/(end_time-begin_time), wave_type)
    
def find_points(waves, points, begin_time, end_time, 
                procedure, arguments):
    """Odnajduje punkty na danym zakresie czasu za pomocą podanej 
    procedury.
    """
    if (procedure.required_waves
        and not all(wave in waves for wave in procedure.required_waves)):
        raise ValueError('Nie podano wymaganych przebiegów z %s'
                         % procedure.required_waves)
    if (procedure.required_points
        and not all(points_ in points for points_ in procedure.required_points)):
        raise ValueError('Nie podano wymaganych punktów z %s'
                         % procedure.required_points)
    found_points_x, found_points_y = procedure.execute(
        waves, points,
        begin_time, end_time, 
        arguments)
    return sm.Points(found_points_x, found_points_y, procedure.output_type)

def calculate_parameter(waves, points, time_tuples,
                        procedure, arguments):
    """Przeprowadza procedurę obliczającą wartość parametru na danym 
    Composite_data w danych zakresach czasowych i zwraca utworzony 
    Parameter.
    """
    if (procedure.required_waves
        and not all(wave in waves for wave in procedure.required_waves)):
        raise ValueError('Nie podano wymaganych przebiegów z %s'
                         % procedure.required_waves)
    if (procedure.required_points
        and not all(points_ in points for points_ in procedure.required_points)):
        raise ValueError('Nie podano wymaganych punktów z %s'
                         % procedure.required_points)
    parameter = sm.Parameter(procedure.output_type)
    for begin_time, end_time in time_tuples:
        value = procedure.execute(
            waves, points,
            begin_time, end_time,
            arguments)
        parameter.add_value(begin_time, end_time, value)
    return parameter
