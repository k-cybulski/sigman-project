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
from QtSigman.VisualObjects import VWave

class ActionCancelledError(Exception):
    """Raised when an action is cancelled."""

def loadWave(forbiddenNames):
    """Imports sm.Wave instances from files and opens up a dialog
    window with possible metainformaiton options for each.

    Returns a list of tuples containg Wave, chosen dictType, color and axis.
    """
    fileFilter = ('dat (*.dat);;'
                  'Signal express export(*)')
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    path = fileDialog.getOpenFileNames(filter=fileFilter)

    if path[0] == "":
        raise ActionCancelledError

    setOfWaves = []
    if path[1] == 'dat (*.dat)':
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
    elif path[1] == 'Signal express export(*)':
        for filename in path[0]:
            x, y, name = fm.import_signal_from_signal_express_file(filename)
            for i in range(len(name)):
                wave = sm.Wave(y[i], x[i], name[i], 0) #TODO: move to fm
                wave.offset = 0
                wave.type = name[i]
                #TODO: Check whether the name is already taken
                setOfWaves.append((wave, name[i],
                                   DefaultColors.getColor(name[i]), -1))
                #TODO? Open up metadata dialog

    return setOfWaves

def saveData (data, key = ''):
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.AnyFile)
    fileDialog.setDefaultSuffix('.dat')

    try:
        path = fileDialog.getSaveFileName(directory=key+'.dat' )
        if path[0] == "":
            raise ActionCancelledError
        fm.export(path[0], data)
    except AssertionError:
        pass

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
    #TODO: Update to most recent zyl functionality
    fileFilter = "(*.A00)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)

    path = fileDialog.getOpenFileName(filter=fileFilter)
    if path[0] == "":
        raise ActionCancelledError
    title = path[0].split("/")[-1]
    ex = DataActionWidgets.ModelflowImportDialog(path[0], compositeDataWrapper)
    try:
        data_points = compositeDataWrapper.points[ex.SelectedPoints()]
    except:
        raise ActionCancelledError
    modelflowPoints = []
    if ex.result() == 1:
        if ex.SelectedPointsType() == 0:
            reference_data_type = 'sbp'
        elif ex.SelectedPointsType() == 1:
            reference_data_type = 'dbp'
        else:
            reference_data_type = 'r'
        out_points, out_names = fm.import_modelflow_data(
            ex.PathModelflow(), data_points, reference_data_type)
    else:
        raise ActionCancelledError

    return out_points, out_names

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
    """Object containing all important information from 
    CompositeDataWrapper, but without any Qt signals and graphical 
    information which would make it otherwise unpickle-able.
    """
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
            QW.QMessageBox.warning(None, 'Error', 'Invalid file')

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
    waveKey, pointsDict, beginTime, endTime, procedure, arguments, status = pr
    if status is DataActionStatus.Ok:
        originalWave = compositeDataWrapper.waves[waveKey]
        modifiedWave = analyzer.modify_wave(originalWave, pointsDict,
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
            QW.QMessageBox.warning(None, 'Error', 'Points not found')
            raise ActionCancelledError
    else:
        raise ActionCancelledError

def executeMacro (compositeDataWraper, value):
    #TODO: Docs
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
