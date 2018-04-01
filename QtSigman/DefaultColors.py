import random

defaultColors={'ecg':'C0', 'bp':'C1', 
             'r':'r', 
             'sbp':'#886600', 'dbp':'#AA9900', 'dn':'y',
             'hr':'C2'}

def generateColor(text):
    """Deterministically generates a colour for a given text."""
    random.seed(text)
    return ('#%06X' % random.randint(0,0xFFFFFF))

def getColor(text):
    """Returns a colour for a given text. If it is in `defaultColors`,
    returns its corresponding value. If not, returns the output of 
    `generateColor`.
    """
    if text in defaultColors:
        return defaultColors[text]
    return generateColor(text)
