from scipy import stats
import copy
import numpy as np
from .calculateArea import calculateArea

class linearRegresionFitCurveInDiastole:
    def fit (AP, minAP, Volume, minVolume):
        Pex = copy.deepcopy(AP)
        Pex.type = "linearRegresion Pex"
        for i in range (0,len(Pex.data)):
            Pex.data[i] = 0
        fitedCurve = copy.deepcopy(Volume)
        fitedCurve.type = "linearRegresion Pwk"

        estimateSV = []
        fitParameter = [[],[]]
        if (len(minAP)> len(minVolume)):
            length = len (minVolume.data_x)-1
        else:
            length = len (minAP.data_x)-1

        for i in range (0,length):
            #indexVolume =  int(round(minVolume.data_x[i]/ Volume.sample_length))
             if (minAP.data_x[i+1]<(AP.complete_length+AP.offset))and (minAP.data_x[i]>AP.offset):
                  if (minVolume.data_x[i+1]<(Volume.complete_length+Volume.offset))and (minVolume.data_x[i]>Volume.offset):
                    indexPressure =  int(round(minAP.data_x[i]/ AP.sample_length))

                    pressure = copy.copy(AP.data_slice (minAP.data_x[i], minAP.data_x[i+1]))
                    impedance = copy.copy(Volume.data_slice(minVolume.data_x[i],minVolume.data_x[i+1]))
                    if ((min (pressure)+5)<np.mean(pressure)):
                        startOfDiastole = int(round(len(pressure)*0.4))

                        slope, intercept, r_value, p_value, std_err = stats.linregress(impedance[len(impedance)-startOfDiastole:len(impedance)],pressure[len(pressure)-startOfDiastole:len(pressure)])
                        fitParameter[0].append(slope)
                        fitParameter[1].append(intercept)

                        for j in range (0, len(impedance)):
                            fitedCurve.data[indexPressure+j] = impedance[j] * slope + intercept
                        for j in range (0, len(pressure)):
                            Pex.data[indexPressure+j] = pressure[j]- fitedCurve.data [indexPressure+j]

                        SV = calculateArea.calculate (Pex.data[indexPressure:(indexPressure+len(pressure))],AP.sample_length)
                        estimateSV.append (SV)
                    else:
                        estimateSV.append(estimateSV[len(estimateSV)-1])
        return fitedCurve,Pex,fitParameter, estimateSV

    

   