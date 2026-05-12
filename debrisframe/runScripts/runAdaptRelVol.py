"""
Run adaption of release volme by modifying the release thickness
"""
#TODO: Code bereinigen

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import warnings
import tempfile
import shutil
import logging
import sys

# Local imports
from avaframe.com1DFA import DFAtools as DFAtls
from avaframe.in1Data import getInput as gI
import avaframe.in2Trans.rasterUtils as IOf
from avaframe.in3Utils import cfgUtils, cfgHandling
import avaframe.in3Utils.geoTrans as geoTrans
from avaframe.in3Utils import logUtils
import avaframe.in2Trans.shpConversion as shpConv
from avaframe.com1DFA import com1DFA
import avaframe.com1DFA.com1DFATools as com1DFATools
from debrisframe.c1Tif import c1Tif

def getActRelVol(cfgMain,avaDir, cfgDebris, relThVal):
    '''
    '''

    # initialize logging
    # logUtils.initiateLogger(avaDir, "getReleaseVolume")
    # logging.getLogger().setLevel(logging.CRITICAL)
    logging.disable(logging.WARNING)


    # ------------------------------------------------------------------ #
    # cfgMain aufbauen (wird von com1DFAPreprocess benötigt)
    # ------------------------------------------------------------------ #
    # cfgDebris["MAIN"] = {"avalancheDir": str(avaDir)}

    # Work-Verzeichnis bereinigen falls vorhanden (com1DFAPreprocess benötigt leeres Work-Dir)
    workDir = Path(avaDir) / "Work" / "com1DFA"
    if workDir.exists():
        shutil.rmtree(workDir)
        # print(f"Work-Verzeichnis bereinigt: {workDir}")
    
    # ------------------------------------------------------------------ #
    # Preprocessing: vollständig aufgelöste Konfiguration + Input-Dateien
    # ------------------------------------------------------------------ #
    simDict,_, inputSimFiles, _ = com1DFA.com1DFAPreprocess(cfgMain, cfgInfo=cfgDebris)

    # Erste Simulation als Vorlage nehmen
    cuSimName = list(simDict.keys())[0]
    cfgSim = simDict[cuSimName]["cfgSim"]
    releaseFile = simDict[cuSimName]["relFile"]

    # print(f"Release-Datei:   {releaseFile}")
    # print(f"Simulations-Typ: {simDict[cuSimName]['simType']}")
    # print()

    # outDir für initializeSimulation (kein Schreiben gewünscht, temp-Verzeichnis)
    outDirTmp = Path(tempfile.mkdtemp())

    # ------------------------------------------------------------------ #
    # Volumen für verschiedene Release-Dicken berechnen
    # ------------------------------------------------------------------ #
    rho = cfgSim["GENERAL"].getfloat("rho")
    # print(f"Schneedichte rho = {rho} kg/m³\n")
    # print(f"{'relTh [m]':>12}  {'Volumen [m³]':>14}  {'Masse [kg]':>14}  {'Partikel':>10}")
    # print("-" * 56)

    volumes = {}

    for relTh in relThVal:

        # relTh in der aufgelösten Konfiguration überschreiben
        cfgSim["GENERAL"]["relTh"] = str(relTh)
        # sicherstellen dass Dicke nicht aus Datei/Shapefile kommt
        cfgSim["GENERAL"]["relThFromFile"] = "False"
        cfgSim["GENERAL"]["timeDependentRelease"] = "False"

        # Input-Dateien für diese Simulation vorbereiten
        inputSimFilesSim = inputSimFiles.copy()
        inputSimFilesSim = gI.selectReleaseFile(inputSimFilesSim, simDict[cuSimName]["releaseScenario"])

        # DEM und inputSimLines aufbereiten
        demOri, inputSimLines = com1DFA.prepareInputData(inputSimFilesSim, cfgSim)

        # Dicken auf releaseLine setzen
        _, inputSimLines, _ = com1DFA.prepareReleaseEntrainment(
            cfgSim, inputSimFilesSim["releaseScenario"], inputSimLines
        )

        # Report-Ausgabe in temp-Verzeichnis umleiten
        cfgSim["GENERAL"]["avalancheDir"] = str(outDirTmp)

        # Simulation initialisieren (t=0) → Partikel erzeugen
        particles, *_ = com1DFA.initializeSimulation(
            cfgSim, outDirTmp, demOri, inputSimLines, "getReleaseVolume"
        )

        # avalancheDir wieder zurücksetzen für nächste Iteration
        cfgSim["GENERAL"]["avalancheDir"] = str(avaDir)

        # tatsächliches Simulationsvolumen
        mTot = particles["mTot"]
        volume = mTot / rho
        nPart = particles["nPart"]

        volumes[relTh] = volume
        # print(f"{relTh:>12.2f}  {volume:>14.2f}  {mTot:>14.2f}  {nPart:>10d}")
    
    return volumes

def getDEMPath(avaDir):
    """get the DEM file path from a provided avalanche directory

    Parameters
    ----------
    avaDir : str
        path to avalanche directory

    Returns
    -------
    demFile : str (first element of list)
        full path to DEM .asc/.tif file
    """

    # if more than one .asc / .tif file found throw error
    inputDir = Path(avaDir, "Inputs", 'remeshedRasters')

    if inputDir.is_dir():
        demFile = list(inputDir.glob("*.tif")) + list(inputDir.glob("*.asc"))

    else:
        print('Warning: no remeshed topography available. Original topography is used')
        inputDir = Path(avaDir, "Inputs", 'remeshedRasters')
        demFile = list(inputDir.glob("*.tif")) + list(inputDir.glob("*.asc"))


    if len(demFile) > 1:
        message = "There should be exactly one topography .asc/.tif file in %s/Inputs/" % avaDir
        raise AssertionError(message)

    elif len(demFile) == 0:
        message = "No topography .asc / .tif file in %s/Inputs/" % avaDir
        raise FileNotFoundError(message)

    return demFile[0]

def getInputDataCom1DFA(avaDir):
    """Fetch input datasets required for simulation, duplicated function because
    now fetch all available files simulation type set differently in com1DFA compared
    to com1DFAOrig: TODO: remove duplicate once it is not required anymore

    Parameters
    ----------
    avaDir : str or pathlib object
        path to avalanche directory

    Returns
    -------
    inputSimFiles: dict
        dictionary with all the input files

        - demFile : str (first element of list), list of full path to DEM .asc file
        - relFiles : list, list of full path to release area scenario .shp files
        - secondaryReleaseFile : str, full path to secondary release area .shp file
        - entFile : str, full path to entrainment area .shp file
        - resFile : str, full path to resistance area .shp file
        - entResInfo : flag dict
        - timeDepRelCsv : str, full path to time dependent release values .csv file
        flag if Yes entrainment and/or resistance areas found and used for simulation
        flag True if a Secondary Release file found and activated

    """

    # Set directories for inputs, outputs and current work
    inputDir = Path(avaDir, "Inputs")

    # Set flag if there is an entrainment or resistance area
    entResInfo = {}
    releaseDir = inputDir / "REL"

    relFiles = sorted(
        list(releaseDir.glob("*.shp")) + list(releaseDir.glob("*.tif")) + list(releaseDir.glob("*.asc"))
    )
    relSuffixList = [relF.suffix for relF in relFiles]

    if ".shp" in relSuffixList and (".asc" in relSuffixList or ".tif" in relSuffixList):
        message = "Release area information - use either .shp or .asc/.tif files"
        #log.error(message)
        raise AssertionError(message)
    #else:
        #log.info("Release area files are: %s" % [str(relFilestr) for relFilestr in relFiles])
    entResInfo["relThFileType"] = relFiles[0].suffix
    entResInfo["flagRel"] = "Yes"

    # Initialise secondary release areas
    (
        secondaryReleaseFile,
        entResInfo["flagSecondaryRelease"],
        entResInfo["secondaryRelThFileType"],
    ) = gI.getAndCheckInputFiles(inputDir, "SECREL", "Secondary release", fileExt=["shp", "asc", "tif"])
    #if secondaryReleaseFile:
        #log.info("Secondary release file is: %s" % secondaryReleaseFile)

    # Initialise resistance areas
    resFile, entResInfo["flagRes"], entResInfo["resFileType"] = gI.getAndCheckInputFiles(
        inputDir, "RES", "Resistance", fileExt=["shp", "asc", "tif"]
    )
    #if resFile:
        #log.info("Resistance file is: %s" % resFile)

    # Initialise entrainment areas
    entFile, entResInfo["flagEnt"], entResInfo["entThFileType"] = gI.getAndCheckInputFiles(
        inputDir, "ENT", "Entrainment", fileExt=["shp", "asc", "tif"]
    )
    #if entFile:
        #log.info("Entrainment file is: %s" % entFile)

    # Initialise dam line
    damFile, entResInfo["dam"], _ = gI.getAndCheckInputFiles(inputDir, "DAM", "Dam", fileExt="shp")
    #if damFile:
        #log.info("Dam file is: %s" % damFile)

    # Initialise DEM
    demFile = getDEMPath(avaDir)

    # check if mu frictionParameter  file  is available
    muFile, entResInfo["mu"], _ = gI.getAndCheckInputFiles(
        inputDir, "RASTERS", "mu parameter data", fileExt="raster", fileSuffix="_mu"
    )

    # check if xi frictionParameter file  is available
    xiFile, entResInfo["xi"], _ = gI.getAndCheckInputFiles(
        inputDir, "RASTERS", "xi parameter data", fileExt="raster", fileSuffix="_xi"
    )

    # check if k frictionParameter file  is available
    kFile, entResInfo["k"], _ = gI.getAndCheckInputFiles(
        inputDir, "RASTERS", "k parameter data", fileExt="raster", fileSuffix="_k"
    )

    # check if tauc frictionParameter file  is available
    tauCFile, entResInfo["tauC"], _ = gI.getAndCheckInputFiles(
        inputDir, "RASTERS", "tauC parameter data", fileExt="raster", fileSuffix="_tauc"
    )

    # check if bhd (tree diameter) parameter file is available - forest density (nd) needs to be in RES folder
    bhdFile, entResInfo["bhd"], _ = gI.getAndCheckInputFiles(
        inputDir, "RASTERS", "bhd parameter data", fileExt="raster", fileSuffix="_bhd"
    )

    entResInfo["relRemeshed"] = "No"
    entResInfo["secondaryRelRemeshed"] = "No"
    entResInfo["entRemeshed"] = "No"
    entResInfo["tauCRemeshed"] = "No"
    entResInfo["kRemeshed"] = "No"
    entResInfo["muRemeshed"] = "No"
    entResInfo["xiRemeshed"] = "No"
    entResInfo["resRemeshed"] = "No"
    entResInfo["bhdRemeshed"] = "No"

    timeDepRelCsv, entResInfo["timeDepRelCsv"], _ = gI.getAndCheckInputFiles(
        inputDir, "REL", "Time dependent release parameters (csv)", fileExt="csv"
    )

    # return DEM, first item of release, entrainment and resistance areas
    inputSimFiles = {
        "demFile": demFile,
        "relFiles": relFiles,
        "secondaryRelFile": secondaryReleaseFile,
        "entFile": entFile,
        "resFile": resFile,
        "damFile": damFile,
        "entResInfo": entResInfo,
        "muFile": muFile,
        "xiFile": xiFile,
        "kFile": kFile,
        "tauCFile": tauCFile,
        "bhdFile": bhdFile,
        "timeDepRelCsv": timeDepRelCsv,
    }

    for thFile in ["rel", "secondaryRel", "ent"]:
        if entResInfo["%sThFileType" % thFile] in [".asc", ".tif"]:
            if thFile == "rel":
                inputSimFiles["relThFile"] = relFiles
            else:
                inputSimFiles["%sThFile" % thFile] = inputSimFiles["%sFile" % thFile]
        else:
            inputSimFiles["%sThFile" % thFile] = None

    return inputSimFiles

def getGeomRelVol(avaDir,cfgDebris,relThVal):

    # initialize logging
    # logUtils.initiateLogger(avaDir, "get geometric release volume")
    logging.disable(logging.WARNING)

    cfgGen = cfgDebris['GENERAL']

    # Sicherstellen, dass INPUT-Sektion existiert und relThFile leer ist
    # (leer = Dicke kommt aus cfg["GENERAL"]["relTh"], nicht aus einer Datei)
    if not cfgDebris.has_section("INPUT"):
        cfgDebris.add_section("INPUT")
    cfgDebris["INPUT"]["relThFile"] = ""
    cfgDebris["INPUT"]["secondaryRelThFile"] = ""
    cfgGen["timeDependentRelease"] = "False"
    cfgGen["relThFromFile"] = "False"
    cfgGen["secRelArea"] = "False"

    # read input
    inputSimFiles = getInputDataCom1DFA(avaDir)
    pathToDem = inputSimFiles["demFile"]

    # Erstes Release-Szenario (Shapefile) verwenden
    releaseFile = inputSimFiles["relFiles"][0]
    secondaryReleaseFile = inputSimFiles["secondaryRelFile"]

    volumes = {}

    for relTh in relThVal:

        # relTh in der Konfiguration überschreiben
        cfgDebris["GENERAL"]["relTh"] = str(relTh)

        # fetchRelVolume erwartet cfg als einfaches dict (konvertiert intern zurück zu ConfigParser)
        cfgDict = {section: dict(cfgDebris[section]) for section in cfgDebris.sections()}

        volume = com1DFA.fetchRelVolume(
            releaseFile,
            cfgDict,
            pathToDem,
            secondaryReleaseFile,
        )

        volumes[relTh] = volume

    return volumes

def adaptRelVol(cfgMain,avaDir,cfgDebris,geomRelVol):
    #TODO: optimierte Iteration

    geomTh = list(geomRelVol.keys())

    
    for Th in geomTh:
        actTh = Th
        dTh = 3
        actTh_B = actTh + dTh
        diffTh = 1
        dV_mean = 1
        num = 0
        dV_A = 1

        print('-' * 30, f'Thickness {Th} m', '-' * 30, sep='\n')

        while diffTh > 1e-3 and abs(dV_mean) >= 1:
        # while dV_A > 0 and num < 10:
            num += 1

            actVol_A = getActRelVol(cfgMain,avaDir,cfgDebris,[actTh])
            actTh_A = list(actVol_A.keys())[0]
            dV_A = geomRelVol[Th] - actVol_A[actTh_A]
            

            # # rel. error Method
            # reldV = (abs(dV_A)) / geomRelVol[Th]
            # diffTh = actTh_A * (1 * (1 + reldV) - 1)

            # print(f'{num}. iteration: dV = {dV_A:.2f} m³',
            #       f'dTh: {diffTh:.4f} m',
            #       f'Thickness = {actTh_A:.5f} m',
            #       f'V = {actVol_A[actTh_A]} m³')
            
            # actTh = actTh_A * (1 + reldV)
            # actTh = (actTh_A + actTh) / 2


            # Bisection method
            actVol_B = getActRelVol(cfgMain,avaDir,cfgDebris,[actTh_B])
            dV_B = geomRelVol[Th] - actVol_B[actTh_B]
            actTh_mean = (actTh_A + actTh_B) / 2
            actVol_mean = getActRelVol(cfgMain,avaDir,cfgDebris,[actTh_mean])
            dV_mean = geomRelVol[Th] - actVol_mean[actTh_mean]

            diffTh = abs(actTh_A - actTh_B)

            if np.sign(dV_A) == np.sign(dV_B):
                sys.exit('Location of dV = 0 is not in the current interval!')

            if np.sign(dV_A) != np.sign(dV_mean):
                actTh = actTh_A
            else:
                actTh = actTh_B
            
            actTh_B = actTh_mean
            

            print(f'{num}. iteration: dV = {dV_mean:.2f} m³',
                  f'dTh: {diffTh:.4f} m',
                  f'Thickness = {actTh_mean:.5f} m',
                  f'V = {actVol_mean[actTh_mean]} m³')


  

if __name__ == "__main__":
    # +++++++++REQUIRED+++++++++++++
    # variation of release thickness
    relThVal = [1.268, 1.389, 1.51, 1.63, 1.751]

    # suppress warnings from C:\Users\jlahrssen\AvaFrame\avaframe\in3Utils\cfgUtils.py:1012: PerformanceWarning:
    # TODO: Check?
    warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

    # fetch input directory
    cfgMain = cfgUtils.getGeneralConfig(nameFile=Path("debrisframeCfg.ini"))
    avaDir = cfgMain["MAIN"]["avalancheDir"]

    # Load default input parameters from configuration file and update with override parameters
    c1tifCfg = cfgUtils.getModuleConfig(c1Tif)
    defaultCfg = cfgUtils.getModuleConfig(
        com1DFA, onlyDefault=c1tifCfg["com1DFA_com1DFA_override"].getboolean("defaultConfig")
    )
    cfgDebris,_ = cfgHandling.applyCfgOverride(defaultCfg, c1tifCfg, com1DFA, addModValues=False)

    actVolumes = getActRelVol(cfgMain,avaDir,cfgDebris,relThVal)
    print(f'actual volumes: {actVolumes}')
    geomVolumes = getGeomRelVol(avaDir,cfgDebris,relThVal)
    print(f'geometric volumes: {geomVolumes}')
    print(f'actual release area: {geomVolumes[relThVal[0]]/relThVal[0]:.2f} m²')
    print('=' * 30)
    adaptRelVol(cfgMain,avaDir,cfgDebris,geomVolumes)
