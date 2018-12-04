
from PyQt5 import QtWidgets as QW
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem

from scipy.optimize import curve_fit
import numpy as np

error = 0.0001
max = 50

def removeMaxTau(TauByFit, max):
    for i in range (0,len(TauByFit)):
        if (TauByFit[i]>(max-1)):
            j = i
            while (TauByFit[j]>(max-1)):
                j = j+1
                if (j == len(TauByFit)):
                    j = j-1
                    break
            TauByFit[i] = TauByFit[j]
    return TauByFit

def execute (compositeDataWrapper):
    global error, max
    wave, R, Percent,WZ, nameWave = dialogBox(compositeDataWrapper).show()
    error = float (WZ)
    points = []
    if (len(Percent)>0):
        r_x, taus, P8, gTau, P8byFit, TauByFit = compute (wave,R,Percent)
        points = []
        i = 0;
        for y in taus:
            name = nameWave + " tau " + Percent[i] + "%"
            new = cratePoint(r_x, y, name)
            points.append(new)
            i = i + 1

  
        new = cratePoint(r_x, P8, nameWave + " P8_anal")
        points.append(new) 

        new = cratePoint(r_x, gTau, nameWave + " Tau_anal")
        points.append(new) 

        new = cratePoint(r_x, P8byFit, nameWave + " P8_fit")
        points.append(new) 

        TauByFit = removeMaxTau(TauByFit, max)

        new = cratePoint(r_x, TauByFit, nameWave + " Tau_fit")
        points.append(new) 

    return points, []


def cratePoint (data_x,data_y, type):
    return [data_x,data_y, type]

#funkcje wyliczają P8 i tau bazując na dopasowaniu danych do założonej funkcji
def idealPresureFunction (x, P0, P8, tau):
    return P8+ (P0-P8)*(np.exp(-x/tau))

def fitData(xdata, ydata, maxTau = 20):
    if (len(xdata)>len(ydata)):
        xdata =xdata[0:len(ydata)]
    if (len(xdata)<len(ydata)):
        ydata =ydata[0:len(xdata)]
    if (min(ydata)< 0):
        return [0,0,0], 0.0;
    else:
        try:
            popt, pcov = curve_fit(idealPresureFunction, xdata, ydata, [ydata[0], 20, 1], None, False, True, [[ydata[0],0,0],[ydata[0]+1,ydata[0],maxTau]])
        except ValueError:
            popt = [0,0,0];
            pcov = 0.0;
    return popt, pcov;

#Metody wyliczenie P8 bazując na wiedzy o funkcji
#Dwie metody dopasowania P8
#-Dla idealnego dopasowania tau nie zależy od wycinka na jaki patrzymy
#-wyliczone cisnienie powinno być równe zmierzonemu
#Tau wyliczone jest z pola pod funkcją

def diffTauCalculate (taus):
    diff = 0;
    for i in range (0,len(taus)-1):
        diff = diff + abs(taus[i+1]-taus[i])
    return round(diff,3)

def diffPresureCalculate (taus, P8, pressureValue, endTimePoints):
    diff = 0;
    P0 = pressureValue[len(pressureValue)-1]
    for i in range (0,len(taus)-1):
        Pest = P8 + (P0-P8)*np.exp(-(endTimePoints[i+1]-endTimePoints[0])/taus[i])

        diff = diff + abs(Pest-pressureValue[len(pressureValue)-i-2])
    return round(diff,3)

def estimateP8 (areas, pressureValue, endTimePoints, lastTaus, dt, P8 = 1, baseOn = "pressure"):
    if (P8<0):
        P8 = 1
    global error

    for i in range (0,len(lastTaus)):
         lastTaus[i] = round(lastTaus[i],3)
    if (baseOn == "pressure"):
        difference = diffPresureCalculate (lastTaus, P8, pressureValue, endTimePoints)
    else:
        difference = diffTauCalculate (lastTaus)

    if (pressureValue[len(pressureValue)-1]-pressureValue[0]>1):
        while True:
        
            taus = []
            for j in range (0,len(areas)):
                P8area = round(P8 * (endTimePoints[len(areas)]-endTimePoints[len(areas)-1-j]-2*dt),3)
                tau=((areas[j]-P8area) / (pressureValue[j+1]-pressureValue[0]))
                taus.append(round(tau,3))
            
            if (baseOn == "pressure"):
                newDifference = diffPresureCalculate (taus, P8, pressureValue, endTimePoints)
            else:
                newDifference = diffTauCalculate (taus)

            if (newDifference > difference):
                P8 = P8-1
                break
            else:
                difference = newDifference;
            if (P8>= min (pressureValue)):
                break
            P8 = P8 + 1
    else:
        taus=lastTaus
    mean = 0
    for j in range (0,len(areas)):
                P8area = round(P8 * (endTimePoints[len(areas)]-endTimePoints[len(areas)-1-j]-2*dt),3)
                tau=((areas[j]-P8area) / (pressureValue[j+1]-pressureValue[0]))
                taus.append(round(tau,3))
    l = 0
    for t in taus:        
        mean = mean + t
        l = l + 1
    mean = mean / l
    return P8, mean


def estimateP8baseOnPressure(areas, pressureValue, endTimePoints, lastTaus, dt, P8 = 1):
    P8, mean = estimateP8 (areas, pressureValue, endTimePoints, lastTaus, dt, P8, baseOn = "pressure")
    return P8, mean    

def estimateP8baseOnTau (areas, pressureValue, endTimePoints, lastTaus, dt,P8 = 1):
    P8, mean = estimateP8 (areas, pressureValue, endTimePoints, lastTaus, dt, P8 = 1, baseOn = "tau")
    return P8, mean

def estimateArea (data, sampleTime):
        area = 0
        for j in range (0,len(data)-2):
            area = area + (sampleTime*(data[j]+data[j+1])/2)
        return round(area,4);


#Główna funkcja licząca
def compute (wave, R, Percent):
        r_x = []

        taus = []
        P8s = []
        corectedTau = []

        P8byFit = []
        TauByFit = []
        global max
        for i in range (0,len(Percent)):
            taus.append([])

        if (len(Percent)>1):
            for i in range(0,len(R)-1):
                if (wave.offset<R.data_x[i] and R.data_x[i+1]<(wave.complete_length+wave.offset)):
                    
                    endTimePoints = []
                    for pointT in Percent:
                        pom = float(pointT)/100
                        endTimePoints.append(R.data_x[i+1]-(R.data_x[i+1]-R.data_x[i])*pom-wave.sample_length)
                    endTimePoints.append(R.data_x[i+1]+wave.sample_length)
                    endTimePoints.sort();


                    areas = []
                    pressureValue = []
                    tau = 0
                    for j in range (0,len(endTimePoints)-1):
                        data = wave.data_slice(endTimePoints[len(endTimePoints)-j-2],endTimePoints[len(endTimePoints)-1])
                        area = estimateArea (data, wave.sample_length)
                        if (j==0):
                            areas.append(area)
                            pressureValue.append(data[len(data)-2])
                        else:
                            areas.append(area)
                        pressureValue.append(data[0])
                    
                    time = round(endTimePoints[len(endTimePoints)-1]-endTimePoints[0],3)
                    xdata = np.linspace(0, time, np.floor(time/wave.sample_length))
                    ydata = data = wave.data_slice(endTimePoints[0],endTimePoints[len(endTimePoints)-1]-wave.sample_length)
                    a, b =fitData(xdata, ydata, max)
                    P8byFit.append(a[1])
                        
                    TauByFit.append(a[2])

                    lastTaus = []
                    for j in range (0,len(areas)):
                        if ((pressureValue[j+1]-pressureValue[0]) > 2):
                            tau=(areas[j] / (pressureValue[j+1]-pressureValue[0]))
                            taus[j].append(tau)
                            lastTaus.append(tau)
                        else:
                            if(len(taus[j])>0):
                                taus[j].append(taus[j][len(taus[j])-1])
                                lastTaus.append(taus[j][len(taus[j])-1])
                            else:
                                 taus[j].append(-1)
                                 lastTaus.append(-1)
                    if (i == 0):    
                        P8, goodTau = estimateP8baseOnPressure (areas, pressureValue, endTimePoints, lastTaus,wave.sample_length)   
                    else:
                        P8, goodTau = (estimateP8baseOnPressure (areas, pressureValue, endTimePoints, lastTaus,wave.sample_length, round(P8s[len(P8s)-1]*0.75)))    
                    corectedTau.append(goodTau)
                    P8s.append (P8)
                    
                    r_x.append(R.data_x[i])
                else:
                    break
        return r_x, taus, P8s, corectedTau, P8byFit, TauByFit
    


class dialogBox (QW.QDialog):
    data = []

    go = 0

    def __init__(self, compositeDataWrapper):
        super().__init__()
        global data 
        data = compositeDataWrapper
        self.title = "Estimate time decay"
        self.setWindowTitle(self.title)
        gridLayout = QW.QGridLayout()
        
        self.setLayout(gridLayout)
      
        self.valueLabel = QW.QLabel("Select the signal:")
        gridLayout.addWidget(self.valueLabel,1,1)  

        

        self.valueComboBox = QW.QComboBox()
        self.valueComboBox.addItems(compositeDataWrapper.waves.keys())
        gridLayout.addWidget(self.valueComboBox,2,1)
    
        self.timeLabel = QW.QLabel("Points determining end of diastole decay:")
        gridLayout.addWidget(self.timeLabel,3,1)
        
        self.timePointsComboBox = QW.QComboBox()
        self.timePointsComboBox.addItems(compositeDataWrapper.points.keys())
        gridLayout.addWidget(self.timePointsComboBox,4,1)

        self.PercentLabel = QW.QLabel("Percentage of cardiac cycle taken to the analysis:")
        gridLayout.addWidget(self.PercentLabel,5,1)

        self.PercentLabelBox = QW.QLineEdit ("10, 15, 20")
        gridLayout.addWidget (self.PercentLabelBox,6,1)

        self.WzLabel = QW.QLabel("Coefficient of convergence")
        gridLayout.addWidget(self.WzLabel,7,1)

        self.WzBox = QW.QLineEdit ("0.1")
        gridLayout.addWidget (self.WzBox,8,1)
        

        self.changeButton = QW.QPushButton("Compute")
       
        self.changeButton.clicked.connect(self.endThisAndDo)
        gridLayout.addWidget(self.changeButton,9,1)
        

    def endThisAndDo(self):
        global go
        go = 1
        self.close()

    def show (self):       
       global go 
       go = 0
       self.exec()

       if (go ==1):
           values = self.valueComboBox.currentText()
           wave = data.waves[values]
           nameWave = values
       
           TimePoints = self.timePointsComboBox.currentText()
           R = data.points[TimePoints]

           string = (self.PercentLabelBox.text())
           Percent = string.split(",")

           WZ = (self.WzBox.text())

       else:
            wave = []
            R = []
            Percent = []
            WZ= 0
            nameWave = ""
       return wave, R, Percent, WZ, nameWave

      
     
          

    




