"""Ten moduł zawiera listę podstawowych powiązań różnych rodzajów danych z
kolorami.
"""
defaultColors={'ecg':'C0', 'bp':'C1', 
             'r':'r', 
             'sbp':'#886600', 'dbp':'#AA9900', 'dn':'y',
             'hr':'C2'}

def generateColor(text):
    """Generuje kolor w oparciu o hash tekstu."""
    return hex(abs(hash('a')%0xFFFFFF))

def getColor(text):
    """Zwraca kolor dla danego tekstu. Jeśli jest on w dict
    defaultColors, zwraca odpowiadającą mu wartość. Jeśli nie, to 
    generuje kolor w oparciu o hash tekstu.
    """
    if text in defaultColors:
        return defaultColors[text]
    return generateColor(text)
