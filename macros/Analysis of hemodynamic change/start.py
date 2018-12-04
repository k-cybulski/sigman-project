import xlsxwriter
from PyQt5 import QtWidgets as QW
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem
import bisect
import numpy

def execute (compositeDataWrapper):
    dialogBox(compositeDataWrapper)
    return [], []


class dialogBox (QW.QDialog):
    data = []

    def __init__(self, compositeDataWrapper):
        super().__init__()
        global data 
        data = compositeDataWrapper
        self.title = "Analysis of hemodynamic change"
        self.setWindowTitle(self.title)
        gridLayout = QW.QGridLayout()
        
        self.setLayout(gridLayout)
      
        self.timeLabel = QW.QLabel("Points determining the time: (Markers)")
        gridLayout.addWidget(self.timeLabel,1,1)  

        

        self.timePointsComboBox = QW.QComboBox()
        self.timePointsComboBox.addItems(compositeDataWrapper.points.keys())
        gridLayout.addWidget(self.timePointsComboBox,2,1)
    
        self.valueLabel = QW.QLabel("Points to write to the sheet:")
        gridLayout.addWidget(self.valueLabel,3,1)
        
        self.valueComboBox = QW.QComboBox()
        self.valueComboBox.addItems(compositeDataWrapper.points.keys())
        gridLayout.addWidget(self.valueComboBox,4,1)

        self.minusTimeLabel = QW.QLabel("Averaging time (befor the markers):")
        gridLayout.addWidget(self.minusTimeLabel,5,1)

        self.minusTimeBox = QW.QLineEdit ("1")
        gridLayout.addWidget (self.minusTimeBox,6,1)

        self.plusTimeLabel = QW.QLabel("Averaging time (after the markers):")
        gridLayout.addWidget(self.plusTimeLabel,7,1)

        self.plusTimeBox = QW.QLineEdit ("1")
        gridLayout.addWidget (self.plusTimeBox,8,1)


        
        self.artefactMask = QW.QCheckBox('Use artefact points mask:', self)

        gridLayout.addWidget(self.artefactMask,10,1)
        self.artefactMaskComboBox = QW.QComboBox()
        self.artefactMaskComboBox.addItems(compositeDataWrapper.points.keys())
        gridLayout.addWidget(self.artefactMaskComboBox,11,1)

        self.changeButton = QW.QPushButton("Write points to the sheet")
        self.changeButton.clicked.connect(self.Write)
        gridLayout.addWidget(self.changeButton,12,1)
        
        self.saveButton = QW.QPushButton("Save sheet")
        self.saveButton.clicked.connect(self.Change)
        gridLayout.addWidget(self.saveButton,13,1)
   

        self.tableWidget = QTableWidget()
 
        # set row count
        self.tableWidget.setRowCount(1)
 
        # set column count
        self.tableWidget.setColumnCount(1)
        gridLayout.addWidget(self.tableWidget,1,2,10,2)
      

        self.exec()
        self.show()


    def Write(self):
       # Data can be assigned directly to cells
             
       if (self.tableWidget.rowCount() == 1):
          punktyCzasowe = self.timePointsComboBox.currentText()
          if punktyCzasowe == '':
             return
          self.insertColumn (punktyCzasowe, data.points[punktyCzasowe].data_x, 0)
          self.timePointsComboBox.setEnabled(False)

       mTime = float(self.minusTimeBox.text())
       pTime = float(self.plusTimeBox.text())


       meanData = []
       values = self.valueComboBox.currentText()
       for i in range (1,self.tableWidget.rowCount()):
           startTime = float(self.tableWidget.item(i,0).text())-mTime
           endTime = float(self.tableWidget.item(i,0).text())+pTime
           minIndex = bisect.bisect_right (data.points[values].data_x,startTime)
           maxIndex = bisect.bisect_left (data.points[values].data_x,endTime)

           if ((maxIndex-minIndex)>0):
               if (self.artefactMask.isChecked() == False):
                   sum = 0;
                   for j in range (minIndex,maxIndex):
                       sum = sum + data.points[values].data_y[j]
                   sum = sum / (maxIndex-minIndex)
                   meanData.append(sum)                   
               else:

                   maskName = self.artefactMaskComboBox.currentText()
                   xTime, mask = data.points[maskName].data_slice(startTime,endTime)
                   self.artefactMaskComboBox.setEnabled(False)
                   
                   data_table = [];


                   for j in range (minIndex,maxIndex):
                       if ((j-minIndex)<len(mask)):
                           if (mask[j-minIndex]==1):
                               data_table.append(data.points[values].data_y[j])
                   
                   if (len(data_table)>0):
                       meanData.append(numpy.mean(data_table))
                   else:
                       meanData.append("NAN")
                   
           else:
               meanData.append("NAN")
           
       self.insertColumn (values, meanData, self.tableWidget.columnCount())
      
     
          

    def insertColumn (self,name, rowData, columnNumber):
          
          if (columnNumber == 0):
              self.tableWidget.setRowCount = len(rowData)
          else:
              self.tableWidget.insertColumn(self.tableWidget.columnCount())

          naglowek = QTableWidgetItem()
          self.tableWidget.setItem (0,columnNumber, naglowek)
          naglowek.setText(name)

          item = []
          for i in range(1,len(rowData)+1):
              item = QTableWidgetItem()
              if (self.tableWidget.rowCount()<len(rowData)+1):
                  self.tableWidget.insertRow(i)
              self.tableWidget.setItem (i, columnNumber, item)
              item.setText(str(rowData[i-1]))

    def Change(self):
       fileFilter = ('xlsx file (*.xlsx);; '
                        'all_files (*)')

       fileDialog = QW.QFileDialog()
       newpath = fileDialog.getSaveFileName(filter = fileFilter)
       workbook = xlsxwriter.Workbook(newpath[0])
       worksheet = workbook.add_worksheet()
       for i in range (0,self.tableWidget.rowCount()):
           for j in range (0,self.tableWidget.columnCount()):
              try:
                 if (i != 0 and (self.tableWidget.item(i,j).text()!= "NAN") and (self.tableWidget.item(i,j).text()!= "inf")):
                     worksheet.write(i,j, float(self.tableWidget.item(i,j).text()))
                 else:
                     worksheet.write(i,j, self.tableWidget.item(i,j).text())
              except:
                 return

       workbook.close()




