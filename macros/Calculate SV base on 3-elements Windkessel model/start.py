from PyQt5 import QtWidgets as QW

from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem

from scipy.integrate import odeint
import numpy as np
import sigman as sm 

# function that returns dy/dt
def modelEquation(y,t,p,dp,r,c,z,dt):
    # u steps from 0 to 2 at t=10
    n = int (np.floor(t/dt))
    if (n >= len(dp)):
        n = len(dp) - 1
    dydt = (((c*dp[n]) + (p[n]/r) - (y*(1 + (z/r)))) / (c*z))  
    return dydt

def computedPdt (P,dt):
    dp = []

    dp.append (P[0])

    for i in range (1,len(P)):
        dp.append ((P[i]-P[i-1])/dt)

    return dp

def computeTimeArray (start, end, dt):
    N = int(np.floor((end-start)/dt))-1
    return np.linspace (0, end-start, N)

def computeStrokeVolume (bloodflow, dt):
    i = 0
    while (bloodflow[i]<0):
        if (i == len(bloodflow)):
            break
        i = i + 1

    SV = 0
    while (bloodflow[i+1]>0):
        SV = SV + (((bloodflow[i+1][0]+bloodflow[i][0]) /2 ) * dt)
        i = i + 1
        if ((i+1) == len(bloodflow)):
            break
    return SV

def execute (compositeDataWrapper):
    resultWaves = []
    points = []
    AP, startOfCycle, Z, C  = dialogBox(compositeDataWrapper).show()
    if (len(AP)> 0):

        nextTPR = 2
        bloodFlow = []
        SV = []
        TPR = []
        xT = []
        for i in range (0,len(startOfCycle)-1):


            print ("%d/%d" % (i, len(startOfCycle)-1))
            # initial condition
            Q0 = 0

            # solve ODE
            r = nextTPR
            c = C.data_y[i]
            z = Z.data_y[i]

            p = AP.data_slice(startOfCycle.data_x[i],startOfCycle.data_x[i+1])
            dp = computedPdt (p,AP.sample_length)
            
            
            # time points
            t = computeTimeArray(startOfCycle.data_x[i],startOfCycle.data_x[i+1],AP.sample_length)
            
            y = odeint(modelEquation,Q0,t,args=(p,dp,r,c,z,AP.sample_length))

            sv = computeStrokeVolume(y,AP.sample_length)
           
            #save data
            nextTPR = np.mean(p) / sv
            TPR.append(nextTPR)
            SV.append (sv)
            xT.append(startOfCycle.data_x[i])
            bloodFlow = np.append (bloodFlow,y)
        #create Wave from data
        waveBloodFlow = sm.Wave (bloodFlow,AP.sample_rate,'BloodFlow_Windkessel',startOfCycle.data_x[0])
        resultWaves.append (waveBloodFlow)

        points.append (cratePoint(xT, SV, 'StrokeVolume_Windkessel'))
        points.append (cratePoint(xT, TPR, 'TotalPeripheralResistance_Windkessel'))
        
    return points, resultWaves

   


def cratePoint (data_x,data_y, type):
    return [data_x,data_y, type]


    


class dialogBox (QW.QDialog):
    data = []

    go = 0

    def __init__(self, compositeDataWrapper):
        super().__init__()
        global data 
        data = compositeDataWrapper
        self.title = "Estimate SV base on three-elements Windkessel model"
        self.setWindowTitle(self.title)
        gridLayout = QW.QGridLayout()
        
        self.setLayout(gridLayout)
      
        self.valueLabel = QW.QLabel("Select blood pressure signal (AP):")
        gridLayout.addWidget(self.valueLabel,1,1)  

        

        self.APComboBox = QW.QComboBox()
        self.APComboBox.addItems(compositeDataWrapper.waves.keys())
        gridLayout.addWidget(self.APComboBox,2,1)

        self.startAPLabel = QW.QLabel("Points specifying the beginning of the cardiac cycle:")
        gridLayout.addWidget(self.startAPLabel,3,1)
        
        self.startAPComboBox = QW.QComboBox()
        self.startAPComboBox.addItems(compositeDataWrapper.points.keys())
        gridLayout.addWidget(self.startAPComboBox,4,1)

        
            
        self.AZLabel = QW.QLabel("Aortic impedance value (Z):")
        gridLayout.addWidget(self.AZLabel,5,1)
        
        self.AZComboBox = QW.QComboBox()
        self.AZComboBox.addItems(compositeDataWrapper.points.keys())
        gridLayout.addWidget(self.AZComboBox,6,1)
        
        self.ACLabel = QW.QLabel("Aortic compilance value (C):")
        gridLayout.addWidget(self.ACLabel,7,1)

        self.ACComboBox = QW.QComboBox()
        self.ACComboBox.addItems(compositeDataWrapper.points.keys())
        gridLayout.addWidget(self.ACComboBox,8,1)
 

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
           values = self.APComboBox.currentText()
           AP = data.waves[values]


           startPoints = self.startAPComboBox.currentText()
           startOfCycle = data.points[startPoints]

           ZPoints = self.AZComboBox.currentText()
           Z = data.points[ZPoints]

           CPoints = self.ACComboBox.currentText()
           C = data.points[CPoints]

       else:
            AP = []
            startOfCycle = []
            Z = []
            C = []

           
       return AP, startOfCycle, Z, C

      
     
          

    




