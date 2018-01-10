"""Ten moduł zawiera listę podstawowych powiązań różnych rodzajów danych z
kolorami.
"""
import random
from random import randint  

defaultColors={'ecg':'C0', 'bp':'C1', 
             'r':'r', 
             'sbp':'#886600', 'dbp':'#AA9900', 'dn':'y',
             'hr':'C2'}

def generateColor(text):
    """Deterministycznie generuje kolor dla danego tekstu."""
    random.seed(text)
    return ('#%06X' % random.randint(0,0xFFFFFF))

def getColor(text):
    """Zwraca kolor dla danego tekstu. Jeśli jest on w dict
    defaultColors, zwraca odpowiadającą mu wartość. Jeśli nie, to 
    deterministycznie generuje kolor w oparciu o tekst.
    """
    if text in defaultColors:
        return defaultColors[text]
    return generateColor(text)

def getColorsArray (count):
     colors = []
     for i in range(count):
             colors.append('#%06X' % randint(0, 0xFFFFFF))
     return colors
