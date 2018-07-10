from os import getcwd
import pickle

from PyQt5 import QtWidgets as QW
from sigman import file_manager as fm
from sigman import analyzer, EmptyPointsError
import sigman as sm
import importlib
import QtSigman
from QtSigman import DataActionWidgets, ImportModelflow, DefaultColors
from QtSigman.DataActionWidgets import DataActionStatus
from QtSigman.MplWidgets import Axis

def importModelflow (compositeDataWrapper):
    fileFilter = ('all_supported_files (*.csv *.A00);; '
            'BeatScope (*.A00);; Finapres Nova (*.csv);; '
            'all_files (*)')
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    
    try:
        path = fileDialog.getOpenFileName(filter = fileFilter)
        assert path[0] != ""
        title = path[0].split("/")[-1]
        ex = DataActionWidgets.ModelflowImportDialog(path[0],compositeDataWrapper)
        status = ex.result()
        if status == 1:
            ModelflowData = fm.import_data_from_modelflow(ex.PathModelflow())
            if '.A00' in ex.PathModelflow():
                if (ex.SelectedPointsType() == 0):
                    FitNumber = 0
                    HR = compositeDataWrapper.points[ex.SelectedPoints()].data_y
                elif (ex.SelectedPointsType() == 1):
                    FitNumber = 1
                    HR = compositeDataWrapper.points[ex.SelectedPoints()].data_y
                else:
                    FitNumber = 6
                    HR = ImportModelflow.DetermineHR(compositeDataWrapper.points[ex.SelectedPoints()].data_x)
                    wave = sm.Points(compositeDataWrapper.points[ex.SelectedPoints()].data_x,HR,'wyznaczoneHRzR')
                    wave.offset = 0
                    wave.type = 'wyznaczoneHRzR'
                    compositeDataWrapper.add_points(wave, 'wyznaczoneHRzR', 
                        color=DefaultColors.getColor('wyznaczoneHRzR'), 
                        axis=Axis.Hidden)

                ModelflowOffset = ImportModelflow.EstimateModelflowDataOffset (ModelflowData[1][FitNumber],HR)
            else:
                 HR = ImportModelflow.DetermineHR(compositeDataWrapper.points[ex.SelectedPoints()].data_x)
                 wave = sm.Points(compositeDataWrapper.points[ex.SelectedPoints()].data_x,HR,'wyznaczoneHRzR')
                 wave.offset = 0
                 wave.type = 'wyznaczoneHRzR'
                 compositeDataWrapper.add_points(wave, 'wyznaczoneHRzR', 
                        color=DefaultColors.getColor('wyznaczoneHRzR'), 
                        axis=Axis.Hidden)

                 ImportFileHR = ImportModelflow.DetermineHR(ModelflowData[0])
                 ModelflowData[1].append(ImportFileHR)
                 ModelflowData[2].append('HR_Modelflow')
                 ModelflowOffset = ImportModelflow.EstimateModelflowDataOffset (ImportFileHR,HR)

            #jesli przesuniecie rowna sie 2 oznacza to ze czas dane[2] ma się równać czasowi HR[0]
            if (ModelflowOffset>0):
                offset =compositeDataWrapper.points[ex.SelectedPoints()].data_x[0] - ModelflowData[0][ModelflowOffset]
                for i in range(len(ModelflowData[0])):
                    ModelflowData[0][i] = ModelflowData[0][i]+offset

            for i in range(len(ModelflowData[2])-1):
                wave = sm.Points(ModelflowData[0],ModelflowData[1][i], ModelflowData[2][i+1])
                wave.offset = 0
                wave.type = ModelflowData[2][i+1]
                #TODO: dodać sprawdzenie czy etykieta nie została zajęta
                compositeDataWrapper.add_points(wave, ModelflowData[2][i+1], 
                    color=DefaultColors.getColor(ModelflowData[2][i+1]), 
                    axis=Axis.Hidden)
    # W wypadku, gdy plik nie zostanie wybrany, po prostu udajemy że nic się
    # nie stało i nic nie zmieniamy
    except AssertionError:
        pass


def importWave(compositeDataWrapper):
    fileFilter = ('dat (*.dat);;'
                  'Signal express export(*)')
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    try:
        path = fileDialog.getOpenFileNames(filter = fileFilter)
        assert path[0] != ""

        if (path[1]== 'dat (*.dat)'):
            for s in path[0]:
                title = s.split("/")[-1]
                title = title.split (".")[0]
                wave = fm.import_wave(s, 'default')
                wave.offset = 0
                wave.type = title
                compositeDataWrapper.add_wave(wave, title, 
                    color=DefaultColors.getColor(title), axis=Axis.Hidden)
        else:
            for s in path[0]:
                x,y, name = fm.import_signal_from_signal_express_file(s)
                for i in range(len(name)):
                    wave = sm.Wave(y[i], x[-1],name[i],0)
                    wave.offset = 0
                    wave.type = name[i]
                #TODO: dodać sprawdzenie czy etykieta nie została zajęta
                    compositeDataWrapper.add_wave(wave, name[i], 
                        color=DefaultColors.getColor(name[i]), 
                        axis=Axis.Hidden)

    # W wypadku, gdy plik nie zostanie wybrany, po prostu udajemy że nic się
    # nie stało i nic nie zmieniamy
    except AssertionError:
        pass

def importPoints(compositeDataWrapper):
    fileFilter = "dat (*.dat)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    try:
        path = fileDialog.getOpenFileNames(filter = fileFilter)
        assert path[0] != ""
        for s in path[0]:
            name = s.split("/")[-1]
            name = name.split (".")[0]
            points = fm.import_points(s, name)
            if name in compositeDataWrapper.points.keys():
                dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
                    forbiddenNames = compositeDataWrapper.points.keys(),
                    dictType=name,
                    title = path[0],
                    color=DefaultColors.getColor(name))
                if status is DataActionStatus.Ok:
                    points.move_in_time(offset)
                    points.type = dictType
                    compositeDataWrapper.add_points(points, dictType, 
                                                    color=color, axis=axis)
            else:
                compositeDataWrapper.add_points(points, name, 
                                                    color=DefaultColors.getColor(name), axis=Axis.Hidden)
    # W wypadku, gdy plik nie zostanie wybrany, po prostu udajemy że nic się
    # nie stało i nic nie zmieniamy
    except AssertionError:
        pass

def saveData (data_x, data_y, key = ''):
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.AnyFile)
    fileDialog.setDefaultSuffix('.dat')

    try:
        path = fileDialog.getSaveFileName(directory = key+'.dat' )
        assert path[0] != ""
        dataLen = 0;
        if (len(data_x)>len(data_y)):
            dataLen = len(data_y)
        else:
            dataLen = len(data_x)
        with open(path[0],'w') as file:
            for i in range (0,dataLen):
                file.write(str(data_x[i]))
                file.write ('  ')
                file.write(str(data_y[i]))
                file.write('\n')
        file.close()
    except AssertionError:
        pass

def inputWaveSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.waves.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.waves[dictType].axis,
        offset = str(compositeDataWrapper.waves[dictType].offset),
        askDelete = True,
        color = compositeDataWrapper.waves[dictType].color)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.editWaveSettings(
            dictType, newDictType, color, axis, offset)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_wave(dictType)

def inputPointSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.points.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.points[dictType].axis,
        askDelete = True,
        color = compositeDataWrapper.points[dictType].color)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.editPointsSettings(
            dictType, newDictType, color, axis, offset)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_points(dictType)

def inputParameterSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.parameters.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.parameters[dictType].axis,
        askDelete = True,
        color = compositeDataWrapper.parameters[dictType].color,
        offset = None)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.inputParameterSettings(
            dictType, newDictType, color, axis)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_parameter(dictType)

class _PickledCompositeDataWrapper:
    """Obiekt zawierający wszystkie kluczowe informacje zawarte w 
    CompositeDataWrapper, lecz bez sygnałów Qt oraz informacji
    graficznych które uniemożliwiają użycie na nim pickle."""
    def __init__(self, compositeDataWrapper):
        data = [
            compositeDataWrapper.waves,
            compositeDataWrapper.points,
            compositeDataWrapper.parameters]
#       mplObject każdego obiektu danych powinien być usunięty, by nie
#       przeszkadzać przy wczytywaniu, lecz jeśli zostanie to zrobione przy
#       zapisywaniu to obecnie wyświetlone dane znikną. Zamiast tego jest to
#       robione w trakcie wczytywania
#        for dataItem in data:
#            for key, item in dataItem.items():
#                item.removeMplObject()
        self.waves = compositeDataWrapper.waves
        self.points = compositeDataWrapper.points
        self.parameters = compositeDataWrapper.parameters

def loadCompositeData():
    fileFilter = "pickle (*.pickle)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    try:
        path = fileDialog.getOpenFileName(filter = fileFilter)
        assert path[0] != ""
        with open(path[0], 'rb') as pickleFile:
            compositeData = pickle.load(pickleFile)
            if isinstance(compositeData, sm.Composite_data):
                return QtSigman.CompositeDataWrapper.fromSigmanCompositeData(compositeData)
            elif (isinstance(compositeData, QtSigman.CompositeDataWrapper) or
                  isinstance(compositeData, _PickledCompositeDataWrapper)):
                return compositeData
            else:
                msg = QW.QMessageBox()
                msg.setIcon(QW.QMessageBox.Warning)
                msg.setText("Niewłaściwy plik.")
                msg.exec_()
    # W wypadku, gdy plik nie zostanie wybrany, po prostu udajemy że nic się
    # nie stało i nic nie zmieniamy
    except AssertionError:
        pass

def saveCompositeData(compositeData):
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.AnyFile)
    fileDialog.setDefaultSuffix('.pickle')
    try:
        path = fileDialog.getSaveFileName()
        assert path[0] != ""
        with open(path[0], 'wb') as pickleFile:
            pickledData = _PickledCompositeDataWrapper(compositeData)
            pickle.dump(pickledData, pickleFile)
    except AssertionError:
        pass

def modifyWave(compositeDataWrapper):
    pr = DataActionWidgets.ProcedureDialog.getProcedure(
        'modify', compositeDataWrapper)
    waveKey, pointsDict, beginTime, endTime, procedure, arguments, status = pr
    if status is DataActionStatus.Ok:
        originalWave = compositeDataWrapper.waves[waveKey]
        modifiedWave = analyzer.modify_wave(originalWave, pointsDict,
                                            beginTime, endTime, 
                                            procedure, arguments)
        if status is DataActionStatus.Cancel:
            return
        compositeDataWrapper.waves[waveKey].replace_slice(
            beginTime, endTime, modifiedWave)
        compositeDataWrapper.waveChanged.emit()

def findPoints(compositeDataWrapper):
    pr = DataActionWidgets.ProcedureDialog.getProcedure(
        'points', compositeDataWrapper)
    waveDict, pointsDict, beginTime, endTime, procedure, arguments, status = pr
    if status is DataActionStatus.Ok:
        try:
            newPoints = analyzer.find_points(waveDict, pointsDict, 
                                             beginTime, endTime, 
                                             procedure, arguments)
            nameBase = 'found_points'
            nameNum = 0
            name = nameBase + str(nameNum)
            while name in compositeDataWrapper.points:
                nameNum += 1
                name = nameBase + str(nameNum)
            dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
                forbiddenNames = compositeDataWrapper.points.keys(),
                title=procedure.__name__)
            if status is DataActionStatus.Cancel:
                return
            compositeDataWrapper.add_points(newPoints, dictType, 
                                            color=color, axis=axis)
        except EmptyPointsError:
            QW.QMessageBox.warning(None, 'Błąd', 'Nie odnaleziono punktów')



def executeMacro (compositeDataWraper, value):
    path = "macros"
    macro = (importlib.import_module (path+'.'+value+'.start'))
    [points, wave] = macro.execute(compositeDataWraper)
    if (len(points)>0):
        for p in points:
            newPoints = sm.Points(p[0],p[1], p[2])
            if (p[2] in compositeDataWraper.points.keys()):            
                dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
                        forbiddenNames = compositeDataWraper.points.keys(),
                        title=p[2])
                if status is DataActionStatus.Cancel:
                    return
            else:
                dictType = p[2]
                color=DefaultColors.getColor(p[2])
                axis=Axis.Hidden 
            compositeDataWraper.add_points(newPoints, dictType, 
                                                color=color, axis=axis)
    if (len(wave)>0):
        for w in wave:
            compositeDataWraper.add_wave(w, w.type, 
                        color=DefaultColors.getColor(w.type), 
                        axis=Axis.Hidden)
