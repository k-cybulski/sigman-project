from PyQt5 import QtWidgets as QW

from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem
from .classes.fitCurveMinMax import fitCurveMinMax
from .classes.linearRegresionFitCurveInDiastole import linearRegresionFitCurveInDiastole





def execute (compositeDataWrapper):
    resultWaves = []
    points = []
    AP, minAP, Volume, minV, state = dialogBox(compositeDataWrapper).show()
    if (len(AP)> 0):
        if state[0][0]:
            fitedCurveMinMax,PexMinMax,fitParameterMinMax, estimateSV = fitCurveMinMax.fit(AP, minAP, Volume, minV)
            resultWaves.append (fitedCurveMinMax)
            resultWaves.append (PexMinMax)
            points.append (cratePoint(minAP.data_x, estimateSV, "MinMax Pole pod Pex (~SV)"))
        if state[1][0]:
            fitedCurveLinear,PexLinear,fitParameterLinear, estimateSV = linearRegresionFitCurveInDiastole.fit(AP, minAP, Volume, minV)
            resultWaves.append (fitedCurveLinear)
            resultWaves.append (PexLinear)
            points.append (cratePoint(minAP.data_x, estimateSV, "linearRegresion Pole pod Pex (~SV)"))

        return points, resultWaves

    return [], []


def cratePoint (data_x,data_y, type):
    return [data_x,data_y, type]


    


class dialogBox (QW.QDialog):
    data = []

    go = 0

    def __init__(self, compositeDataWrapper):
        super().__init__()
        global data 
        data = compositeDataWrapper
        self.title = "Estimate SV base on Reservoir-Wave model"
        self.setWindowTitle(self.title)
        gridLayout = QW.QGridLayout()
        
        self.setLayout(gridLayout)
      
        self.valueLabel = QW.QLabel("Select blood pressure signal (AP):")
        gridLayout.addWidget(self.valueLabel,1,1)  

        

        self.APComboBox = QW.QComboBox()
        self.APComboBox.addItems(compositeDataWrapper.waves.keys())
        gridLayout.addWidget(self.APComboBox,2,1)

        self.startAPLabel = QW.QLabel("Points specifying the beginning of ejection in the pressure signal:")
        gridLayout.addWidget(self.startAPLabel,3,1)
        
        self.startAPComboBox = QW.QComboBox()
        self.startAPComboBox.addItems(compositeDataWrapper.points.keys())
        gridLayout.addWidget(self.startAPComboBox,4,1)

        self.volumeLabel = QW.QLabel("Select volume signal (delta Z):")
        gridLayout.addWidget(self.volumeLabel,5,1)

        self.volumeComboBox = QW.QComboBox()
        self.volumeComboBox.addItems(compositeDataWrapper.waves.keys())
        gridLayout.addWidget(self.volumeComboBox,6,1)
        
            
        self.startVLabel = QW.QLabel("Points specifying the beginning of ejection in the volume signal:")
        gridLayout.addWidget(self.startVLabel,7,1)
        
        self.startVComboBox = QW.QComboBox()
        self.startVComboBox.addItems(compositeDataWrapper.points.keys())
        gridLayout.addWidget(self.startVComboBox,8,1)

        self.minMax = QW.QCheckBox('Fit base on beginning and end of the ejection', self)
        self.minMax.toggle()
        gridLayout.addWidget(self.minMax,9,1)
        
        self.linearRegresion = QW.QCheckBox('Fit curve use linear regresion on diastolic', self)
        self.linearRegresion.toggle()
        gridLayout.addWidget(self.linearRegresion,10,1)

        self.baseOnC = QW.QCheckBox('Fit base on compliance', self)
        self.baseOnC.toggle()
        gridLayout.addWidget(self.baseOnC,11,1)





        self.changeButton = QW.QPushButton("Wylicz wartości")
        #TODO: zablokować obliczenia gdy nie naciśnięto ok.
        self.changeButton.clicked.connect(self.endThisAndDo)
        gridLayout.addWidget(self.changeButton,12,1)
        

    def endThisAndDo(self):
        global go
        go = 1
        self.close()

    def show (self):       
       global go 
       go = 0
       self.exec()

       if (go ==1):
           values = self.APComboBox.currentText()
           AP = data.waves[values]
       
           values = self.volumeComboBox.currentText()
           Volume = data.waves[values]

           startVPoints = self.startVComboBox.currentText()
           minV = data.points[startVPoints]

           startAP = self.startAPComboBox.currentText()
           minAP = data.points[startAP]
           state = [[self.minMax.isChecked()],[self.linearRegresion.isChecked()],[self.baseOnC.isChecked()]]
       else:
            AP = []
            minAP = []
            Volume = []
            minV = []
            state = [[False],[False],[False]]
           
       return AP, minAP, Volume, minV, state

      
     
          

    




