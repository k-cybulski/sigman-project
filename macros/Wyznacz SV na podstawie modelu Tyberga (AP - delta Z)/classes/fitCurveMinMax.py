import numpy as np
import copy
from .calculateArea import calculateArea

class fitCurveMinMax:
    def fit (AP, minAP, Volume, minVolume):

        Pex = copy.deepcopy(AP)
        Pex.type = "MinMax Pex"
        for i in range (0,len(Pex.data)):
             Pex.data[i] = 0
        fitedCurve = copy.deepcopy(Volume)
        fitedCurve.type = "MinMax Pwk"

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
                        
                        
                        pom = fitCurveMinMax.maximum(pressure[0:int(round((len(pressure)/2)))])
                        pom2 = fitCurveMinMax.minimum (pressure[0:int(round((len(pressure)*0.6)))],pom+5)
                        Ya = pressure[0]
                        x2 = int(round((pom + pom2) /2))
                        Yb = pressure[x2]

                        x1 = fitCurveMinMax.maximum(impedance[0:int(round((len(impedance)/2)))])

                        d = x2 - x1
                        impedanceInCycle = copy.deepcopy(Volume.data_slice(minVolume.data_x[i]-(d*Volume.sample_length),minVolume.data_x[i+1])-(d*Volume.sample_length))
                        
                        Xa = impedanceInCycle[0]
                        Xb = impedanceInCycle[x2]
                        

                        a, b = fitCurveMinMax.linearFunctionFit (Ya, Xa, Yb, Xb)
                        fitParameter[0].append(a)
                        fitParameter[1].append(b)

                        for j in range (0, len(impedanceInCycle)):
                            fitedCurve.data[indexPressure+j] = impedanceInCycle[j] * a + b
                        for j in range (0, len(pressure)):
                            Pex.data[indexPressure+j] = pressure[j]- fitedCurve.data [indexPressure+j]

                        SV = calculateArea.calculate (Pex.data[(indexPressure+3):(indexPressure+len(pressure))],AP.sample_length)
                        estimateSV.append (SV)
                    else:
                        if (len(estimateSV)>0):
                            estimateSV.append(estimateSV[len(estimateSV)-1])

        return fitedCurve,Pex,fitParameter, estimateSV

    def maximum (data):
        if len(data)>0:
            m = max (data)
            itemindex = np.where(data==m)[0]
            if (len(itemindex)>1):
                wynik = itemindex[len(itemindex)-1]
            else:
                wynik = itemindex[0]
            return wynik
        else:
            return 0

    def minimum (data,start,LP = 5):
        itemindex = start
        while (np.sum(data[(itemindex-LP):itemindex])>np.sum(data[itemindex:(itemindex+LP)])):
           itemindex = itemindex+1
           if itemindex==(len(data)-LP):
                break
        return itemindex

    def linearFunctionFit (Ya, Xa, Yb, Xb):
        if (Xa is not Xb):
            a = (Ya-Yb)/(Xa-Xb)
        else:
            a = 0
        b = Ya - (a*Xa)
        return a, b