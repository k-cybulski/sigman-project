
from PyQt5 import QtWidgets as QW
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem

import sigman as sm
import numpy as np
import math
def CheckEqualityofPointsLength (pointsList):
    l = len(pointsList[0].data_x)
    equality = True
    for p in pointsList:
        if (len(p) != l):
            equality = False
    return equality

def cratePoint (data_x,data_y, type):
    return [data_x,data_y, type]

def findCommbinedTime (pontsList):
    min = pontsList[0].data_x[0]
    max = pontsList[0].data_x[-1]
    for i in range (1,len(pontsList)):
        if (min<pontsList[i].data_x[0]):
            min = pontsList[i].data_x[0]

        if (max> pontsList[i].data_x[-1]):
            max = pontsList[i].data_x[-1]
        if (min>max):
            break
    min = min + 0.1
    max = max - 0.1
    return min, max

def alignPointsTime (pointsList, min, max):
    resList = []
    for p in pointsList:
        newPointsIndexs = p.slice_range(min,max)
        x, y = p[newPointsIndexs]
        newPoint = sm.Points (x, y, p.type)
        resList.append (newPoint)
    return resList

def execute (compositeDataWrapper):

    pointsList = dialogBox(compositeDataWrapper).show()
   
    points = []

    if (len(pointsList)>0):
        if (CheckEqualityofPointsLength (pointsList)):
            r_x, r_y = compute (pointsList)
            mask = cratePoint(r_x, r_y, "Outliers_mask")
            points.append(mask) 
        else:
            min, max = findCommbinedTime (pointsList)
            pointsList = alignPointsTime(pointsList, min, max)
            if (CheckEqualityofPointsLength (pointsList)):
                r_x, r_y = compute (pointsList)
                mask = cratePoint(r_x, r_y, "Outliers_mask")
                points.append(mask) 
            else:
                msg = QW.QMessageBox ()
                msg.setText ("All points must have the same length")
                msg.setStandardButtons(QW.QMessageBox.Ok)
                msg.exec_()

    return points, []


def createReference (points):
    means = []
    stds = []
    for p in points:
        means.append(np.mean(p.data_y))
        stds.append(np.std(p.data_y))
    res_std = np.mean(stds)*1.96
    return means, res_std

#Główna funkcja licząca
def compute (pointsList):
       r_x = pointsList[0].data_x
       r_y = []
       
       globMeans, globSTD = createReference (pointsList)
       
       N = len(pointsList[0].data_x)
       for i in range(0,N):
           distance = 0
           for j in range (0, len(pointsList)):
               distance = distance + math.pow(pointsList[j].data_y[i]-globMeans[j],2)
           if (distance>globSTD):
                r_y.append(0)
           else:
                r_y.append(1)
       return r_x, r_y
    


class dialogBox (QW.QDialog):

    
    go = 0
    checkBoxs = []
    

    def __init__(self, compositeDataWrapper):
        super().__init__()
        global data
        self.checkBoxs = []
        data = compositeDataWrapper
        self.title = "Kill outlaws - find outliers points"
        self.setWindowTitle(self.title)
        gridLayout = QW.QGridLayout()
        
        self.setLayout(gridLayout)
      
   
        
      

        self.valueLabel = QW.QLabel("Select the points:")
        gridLayout.addWidget(self.valueLabel,1,1)
        
        i = 2
        for name in compositeDataWrapper.points.keys():
            self.force = QW.QCheckBox(name)
            self.force.setCheckState(False)
            self.checkBoxs.append (self.force)
            gridLayout.addWidget(self.force,i,1)
            i = i + 1
    

        

        self.changeButton = QW.QPushButton("Compute")
       
        self.changeButton.clicked.connect(self.endThisAndDo)
        gridLayout.addWidget(self.changeButton,i,1)
        

    def endThisAndDo(self):

        self.go = 1
        self.close()

    def show (self):       
       self.go = 0
       

       self.exec()

       pointsList = []
       startPoints = []
       if (self.go ==1):
           for i in range (0,len(self.checkBoxs)):
               if (self.checkBoxs[i].isChecked()):
                   name = self.checkBoxs[i].text()
                   p = data.points[name]
                   pointsList.append(p)



     
       return pointsList

      
     
          

    




