from os import getcwd
import pickle

from PyQt5 import QtWidgets as QW
from sigman import file_manager as fm
from sigman import analyzer, EmptyPointsError
import sigman as sm


import QtSigman
from QtSigman import DataActionWidgets
from QtSigman.DataActionWidgets import DataActionStatus
from QtSigman.MplWidgets import Axis

from QtSigman import DefaultColors

import numpy as np




def EstimateModelflowDataOffset (ModelflowData, Points):
    differences = []
    difference = 0

    for i in range(0,len(ModelflowData)-len(Points)):
        difference = 0
        for j in range (0,len(Points)):
             difference = difference + abs((ModelflowData[i+j]-Points[j]))     
        differences.append(difference)

    offset = (np.argmin(differences))
    return offset

def DetermineHR (czas):
    HR = [0 for i in range (len(czas)-1)]
    for i in range(len(czas)-1):
        HR[i] =round(60 / (czas[i+1] - czas [i]))
    return HR






   
