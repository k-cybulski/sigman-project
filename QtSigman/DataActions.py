from os import getcwd
import pickle

from PyQt5 import QtWidgets as QW
from sigman import file_manager as fm
from sigman import analyzer, EmptyPointsError
import sigman as sm

import QtSigman
from QtSigman import DataActionWidgets, ImportModelflow, DefaultColors
from QtSigman.DataActionWidgets import DataActionStatus
from QtSigman.VisualObjects import VWave

class ActionCancelledError(Exception):
    """Raised when an action is cancelled."""

def loadWave(forbiddenNames):
    """Imports sm.Wave instances from files and opens up a dialog
    window with possible metainformaiton options for each.

    Returns a list of tuples containg Wave, chosen dictType, color and axis.
    """
    fileFilter = "dat (*.dat)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    path = fileDialog.getOpenFileNames(filter=fileFilter)

    if path[0] == "":
        raise ActionCancelledError

    setOfWaves = []
    for filename in path[0]:
        title = filename.split("/")[-1]
        title = title.split (".")[0]
        wave = fm.import_wave(filename, 'default')
        dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
            forbiddenNames=forbiddenNames,
            title=title)
        if status is DataActionStatus.Ok:
            wave.offset = offset
            wave.type = dictType
            setOfWaves.append((wave, dictType, color, axis))
        else:
            raise ActionCancelledError
    return setOfWaves

def loadPoints(forbiddenNames):
    """Imports sm.Points instances from files and opens up a dialog
    window with possible metainformaiton options for each.

    Returns a list of tuples containing Points, chosen dictType, color and axis.
    """
    fileFilter = "dat (*.dat)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    path = fileDialog.getOpenFileNames(filter=fileFilter)

    if path[0] == "":
        raise ActionCancelledError

    setOfPoints = []
    for filename in path[0]:
        title = filename.split("/")[-1]
        title = title.split (".")[0]        
        points = fm.import_points(filename, 'default')
        dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
            forbiddenNames=forbiddenNames,
            title=title)
        if status is DataActionStatus.Ok:
            points.move_in_time(offset)
            points.type = dictType
            setOfPoints.append((points, dictType, color, axis))
        else:
            raise ActionCancelledError
    return setOfPoints

def loadModelflow(compositeDataWrapper):
    """Import modelflow data and returns tuple consisting of
    modelflowPoints and modelflowData.
    """
    fileFilter = "(*.A00)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)

    path = fileDialog.getOpenFileName(filter=fileFilter)
    if path[0] == "":
        raise ActionCancelledError
    title = path[0].split("/")[-1]
    ex = DataActionWidgets.ModelflowImportDialog(path[0], compositeDataWrapper)
    try:
        dataX = compositeDataWrapper.points[ex.SelectedPoints()].data_x
        dataY = compositeDataWrapper.points[ex.SelectedPoints()].data_y
    except:
        raise ActionCancelledError
    modelflowPoints = None
    HRfromR = None
    if ex.result() == 1:
        modelflowData = fm.import_data_from_modelflow(ex.PathModelflow())
        if ex.SelectedPointsType() == 0:
            FitNumber = 0
            HR = dataY
        elif ex.SelectedPointsType() == 1:
            FitNumber = 1
            HR = dataY
        else:
            FitNumber = 6
            HR = ImportModelflow.DetermineHR(dataX)
            wave = sm.Points(dataX, HR, 'wyznaczoneHRzR')
            wave.offset = 0
            wave.type = 'wyznaczoneHRzR'
            HRfromR = (wave, 'wyznaczoneHRzR')

        modelflowOffset = ImportModelflow.EstimateModelflowDataOffset(
                modelflowData[1][FitNumber], HR)

        # Jesli przesuniecie rowna sie 2 oznacza to 
        # ze czas dane[2] ma się równać czasowi HR[0]
        if modelflowOffset > 0:
            offset = dataX[0] - modelflowData[0][modelflowOffset]
            for i in range(len(modelflowData[0])):
                modelflowData[0][i] = modelflowData[0][i] + offset

        # Zbior zbiorow punktow
        modelflowPoints = []
        for i in range(len(modelflowData[1])-1):
            wave = sm.Points(modelflowData[0], 
                            modelflowData[1][i],
                            modelflowData[2][i+1])
            wave.offset = 0
            wave.type = modelflowData[2][i+1]
            modelflowPoints.append(wave)

    if modelflowPoints is None:
        raise ActionCancelledError

    return (modelflowPoints, modelflowData, HRfromR)

def setVWaveSettings(vWave, key, allKeys):
    forbiddenKeys = list(allKeys)
    forbiddenKeys.remove(key)
    newKey, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames=forbiddenKeys,
        dictType=key,
        title=key,
        axis=vWave.axis,
        offset=str(vWave.data.offset),
        askDelete=True,
        color=vWave.color)
    if status is DataActionStatus.Ok:
        vWave.setSettings(color, axis)
        vWave.data.type = newKey
        vWave.data.offset = offset
        vWave.data.changed.emit()
        vWave.setDictKey(newKey)
    if status is DataActionStatus.Delete:
        vWave.delete()

def setVPointsSettings(vPoints, key, allKeys):
    forbiddenKeys = list(allKeys)
    forbiddenKeys.remove(key)
    newKey, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames=forbiddenKeys,
        dictType=key,
        title=key,
        axis=vPoints.axis,
        offset="0",
        askDelete=True,
        color=vPoints.color)
    if status is DataActionStatus.Ok:
        vPoints.setSettings(color, axis)
        vPoints.data.type = newKey
        vPoints.data.move_in_time(offset)
        vPoints.setDictKey(newKey)
    if status is DataActionStatus.Delete:
        vPoints.delete()

class _PickledCompositeDataWrapper:
    """Obiekt zawierający wszystkie kluczowe informacje zawarte w 
    CompositeDataWrapper, lecz bez sygnałów Qt oraz informacji
    graficznych które uniemożliwiają użycie na nim pickle."""
    def __init__(self, compositeDataWrapper):
        self.waves = {}
        self.points = {}
        self.parameters = {}
        for selfDict, argDict in [
                (self.waves, compositeDataWrapper.waves),
                (self.points, compositeDataWrapper.points),
                (self.parameters, compositeDataWrapper.parameters)]:
            for key, item in argDict.items():
                selfDict[key] = item.copy()

def loadCompositeData():
    fileFilter = "pickle (*.pickle)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    path = fileDialog.getOpenFileName(filter = fileFilter)
    assert path[0] != ""
    if path[0] == "":
        raise ActionCancelledError
    with open(path[0], 'rb') as pickleFile:
        compositeData = pickle.load(pickleFile)
        if (isinstance(compositeData, sm.Composite_data) or
                isinstance(compositeData, QtSigman.CompositeDataWrapper) or
                isinstance(compositeData, _PickledCompositeDataWrapper)):
            return compositeData
        else:
            QW.QMessageBox.warning(None, 'Błąd', 'Niewłaściwy plik')

def saveCompositeData(compositeData):
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.AnyFile)
    fileDialog.setDefaultSuffix('.pickle')
    path = fileDialog.getSaveFileName()
    if path[0] == "":
        raise ActionCancelledError
    with open(path[0], 'wb') as pickleFile:
        pickledData = _PickledCompositeDataWrapper(compositeData)
        pickle.dump(pickledData, pickleFile)

def modifyWave(compositeDataWrapper):
    pr = DataActionWidgets.ProcedureDialog.getProcedure(
        'modify', compositeDataWrapper)
    waveKey, beginTime, endTime, procedure, arguments, status = pr
    if status is DataActionStatus.Ok:
        originalWave = compositeDataWrapper.waves[waveKey]
        modifiedWave = analyzer.modify_wave(originalWave, 
                                            beginTime, endTime, 
                                            procedure, arguments)
        compositeDataWrapper.waves[waveKey].replace_slice(
            beginTime, endTime, modifiedWave)
    else:
        raise ActionCancelledError

def findPoints(compositeDataWrapper):
    pr = DataActionWidgets.ProcedureDialog.getProcedure(
        'points', compositeDataWrapper)
    waveDict, pointsDict, beginTime, endTime, procedure, arguments, status = pr
    if status is DataActionStatus.Ok:
        try:
            newPoints = analyzer.find_points(waveDict, pointsDict, 
                                             beginTime, endTime, 
                                             procedure, arguments)
            dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
                forbiddenNames=compositeDataWrapper.points.keys(),
                title=procedure.__name__)
            if status is DataActionStatus.Cancel:
                raise ActionCancelledError
            newPoints.move_in_time(offset)
            return newPoints, dictType, color, axis
        except EmptyPointsError:
            QW.QMessageBox.warning(None, 'Błąd', 'Nie odnaleziono punktów')
    else:
        raise ActionCancelledError
