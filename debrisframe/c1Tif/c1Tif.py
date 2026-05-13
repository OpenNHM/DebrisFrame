"""
    Debris flow overrides for com1DFA
"""

# Load modules
import logging
import pandas as pd
import pathlib
from itertools import product

# Local imports
from avaframe.in3Utils import cfgUtils
from avaframe.in3Utils import cfgHandling
from avaframe.in1Data import getInput as gI
import avaframe.com1DFA.deriveParameterSet as dP
import avaframe.in2Trans.rasterUtils as IOf
import avaframe.com1DFA.com1DFATools as com1DFATools
from avaframe.com1DFA import checkCfg
from avaframe.com1DFA import com1DFA
from avaframe.com1DFA.com1DFA import getModuleNames, getSimTypeList, setVolumeIndicator, fetchRelVolume

# create local logger under avaframe namespace to use its logging configuration
log = logging.getLogger("avaframe.debrisframe.c1Tif")


def prepareVarSimDict(standardCfg, inputSimFiles, variationDict, simNameExisting="", module=com1DFA):
    """Prepare a dictionary with simulations that shall be run with varying parameters following the variation dict

    Parameters
    -----------
    standardCfg : configParser object
        default configuration or local configuration
    inputSimFiles: dict
        info dict on available input data
    variationDict: dict
        dictionary with parameter to be varied as key and list of it's values
    simNameExisting: list
        list of simulation names that already exist (optional). If provided,
        only carry on simulations that do not exist
    module: module
        module to be used for task (optional)

    Returns
    -------
    simDict: dict
        dictionary with info on simHash, releaseScenario, release area file path,
        simType and contains full configuration configparser object for simulation run
    """

    # extract the full module name and short form (e.g., "com1DFA" -> "com1")
    modName, modNameShort = getModuleNames(module)

    # get list of simulation types that are desired
    if "simTypeList" in variationDict:
        simTypeList = variationDict["simTypeList"]
        del variationDict["simTypeList"]
    else:
        simTypeList = standardCfg["GENERAL"]["simTypeList"].split("|")
    # get a list of simulation types that are desired AND available
    standardCfg, simTypeList = getSimTypeList(standardCfg, simTypeList, inputSimFiles)

    # set simTypeList (that has been checked if available) as parameter in variationDict
    variationDict["simTypeList"] = simTypeList
    # create a dataFrame with all possible combinations of the variationDict values
    variationDF = pd.DataFrame(product(*variationDict.values()), columns=variationDict.keys())

    # generate a dictionary of full simulation info for all simulations to be performed
    # simulation info must contain: simName, releaseScenario, relFile, configuration as dictionary
    simDict = {}

    # loop over all simulations that shall be performed according to variationDF
    # one row per simulation
    log.info("Start working on variations")
    for row in variationDF.itertuples():
        log.info("New line in variationDF-------")
        # convert full configuration to dict
        cfgSim = cfgUtils.convertConfigParserToDict(standardCfg)

        # create release scenario name for simulation name
        rel, cfgSim, relThFile = gI.fetchReleaseFile(
            inputSimFiles,
            row._asdict()["releaseScenario"],
            cfgSim,
            variationDict["releaseScenario"],
        )
        relName = rel.stem
        if "_" in relName:
            relNameSim = relName + "_AF"
        else:
            relNameSim = relName

        # update info for parameters that are given in variationDF
        for parameter in variationDict:
            # add simType
            cfgSim["GENERAL"]["simTypeActual"] = row._asdict()["simTypeList"]
            # update parameter value - now only single value for each parameter
            keyList = [
                "relThPercentVariation",
                "entThPercentVariation",
                "secondaryRelThPercentVariation",
                "relThRangeVariation",
                "entThRangeVariation",
                "secondaryRelThRangeVariation",
                "relThRangeFromCiVariation",
                "entThRangeFromCiVariation",
                "secondaryRelThRangeFromCiVariation",
                "relThDistVariation",
                "entThDistVariation",
                "secondaryRelThDistVariation",
            ]
            if parameter in keyList:
                # set thickness value according to percent variation info
                cfgSim = dP.setThicknessValueFromVariation(
                    parameter, cfgSim, cfgSim["GENERAL"]["simTypeActual"], row
                )
            elif parameter == "releaseScenario":
                cfgSim["INPUT"][parameter] = row._asdict()[parameter]
            else:
                cfgSim["GENERAL"][parameter] = row._asdict()[parameter]

        # update INPUT section - delete non relevant parameters
        if cfgSim["GENERAL"]["simTypeActual"] not in ["ent", "entres"]:
            cfgSim["INPUT"].pop("entrainmentScenario", None)
            cfgSim["INPUT"].pop("entThId", None)
            cfgSim["INPUT"].pop("entThThickness", None)
            cfgSim["INPUT"].pop("entThCi95", None)
        if cfgSim["GENERAL"]["secRelArea"] == "False":
            cfgSim["INPUT"].pop("secondaryReleaseScenario", None)
            cfgSim["INPUT"].pop("secondaryRelThId", None)
            cfgSim["INPUT"].pop("secondaryRelThThickness", None)
            cfgSim["INPUT"].pop("secondaryRelThCi95", None)

        # check if DEM in Inputs has desired mesh size
        pathToDem = dP.checkRasterMeshSize(cfgSim, inputSimFiles["demFile"], "DEM")
        cfgSim["INPUT"]["DEM"] = pathToDem
        dem = IOf.readRaster(pathlib.Path(cfgSim["GENERAL"]["avalancheDir"], "Inputs", pathToDem))

        # check extent of inputs read from raster have correct extent and cellSize
        # first release area
        if inputSimFiles["entResInfo"]["relThFileType"] in [".asc", ".tif"]:
            pathToRel, pathToRelFull, remeshedRel = dP.checkExtentAndCellSize(cfgSim, relThFile, dem, "rel")
            cfgSim["INPUT"]["relThFile"] = pathToRel
            inputSimFiles["entResInfo"]["relRemeshed"] = remeshedRel

        # secondary release area
        if (
            inputSimFiles["entResInfo"]["secondaryRelThFileType"] in [".asc", ".tif"]
            and cfgSim["GENERAL"]["secRelArea"] == "True"
        ):
            pathToSecRel, pathToSecRelFull, remeshedSecRel = dP.checkExtentAndCellSize(
                cfgSim, inputSimFiles["secondaryRelThFile"], dem, "secondaryRel"
            )
            cfgSim["INPUT"]["secondaryRelThFile"] = pathToSecRel
            inputSimFiles["entResInfo"]["secondaryRelRemeshed"] = remeshedSecRel

        if cfgSim["GENERAL"]["timeDependentRelease"] == "True":
            cfgSim["INPUT"]["timeDepRelCsv"] = inputSimFiles["timeDepRelCsv"]
            timeDepRelValues, _ = gI.getTimeDepRelCsv(inputSimFiles["timeDepRelCsv"])
            cfgSim["INPUT"]["timeDepRelTimeStep"] = str(timeDepRelValues["timeStep"])
            cfgSim["INPUT"]["timeDepRelThickness"] = str(timeDepRelValues["thickness"])
            cfgSim["INPUT"]["timeDepRelVelocity"] = str(timeDepRelValues["velocity"])

        if modName in ["com1DFA", "com5SnowSlide", "com6RockAvalanche"]:
            # check if spatialVoellmy is chosen that friction fields have correct extent
            if cfgSim["GENERAL"]["frictModel"].lower() == "spatialvoellmy":
                dem = IOf.readRaster(pathlib.Path(cfgSim["GENERAL"]["avalancheDir"], "Inputs", pathToDem))
                for fric in ["mu", "xi"]:
                    if inputSimFiles["entResInfo"][fric] == "Yes":
                        pathToFric, _, remeshedFric = dP.checkExtentAndCellSize(
                            cfgSim, inputSimFiles["%sFile" % fric], dem, fric
                        )
                        cfgSim["INPUT"]["%sFile" % fric] = pathToFric
                        inputSimFiles["entResInfo"]["%sRemeshed" % fric] = remeshedFric
                    else:
                        message = (
                            "spatialVoellmy friction model: %s file in Inputs/RASTERS with file ending _%s not found"
                            % (fric, fric)
                        )
                        log.error(message)
                        raise FileNotFoundError(message)

            # add info about dam file path to the cfg
            if cfgSim["GENERAL"]["dam"] == "True" and inputSimFiles["damFile"] is not None:
                cfgSim["INPUT"]["DAM"] = str(pathlib.Path("DAM", inputSimFiles["damFile"].name))

        # if tauC, mu, k used in com8 and com9 check extent of cellSize
        if modName in ["com8MoTPSA", "com9MoTVoellmy"]:
            dem = IOf.readRaster(pathlib.Path(cfgSim["GENERAL"]["avalancheDir"], "Inputs", pathToDem))

            if inputSimFiles["entResInfo"]["tauC"] == "Yes":
                pathToFric, pathToFricFull, remeshedFric = dP.checkExtentAndCellSize(
                    cfgSim, inputSimFiles["tauCFile"], dem, "tauC"
                )
                cfgSim["INPUT"]["tauCFile"] = pathToFric
                inputSimFiles["entResInfo"]["tauCRemeshed"] = remeshedFric

            if inputSimFiles["entResInfo"]["bhd"] == "Yes":
                pathToFric, pathToFricFull, remeshedFric = dP.checkExtentAndCellSize(
                    cfgSim, inputSimFiles["bhdFile"], dem, "bhd"
                )
                cfgSim["INPUT"]["bhdFile"] = pathToFric
                inputSimFiles["entResInfo"]["bhdRemeshed"] = remeshedFric

            # check if physical parameters = variable is chosen that friction fields have correct extent
            if cfgSim["Physical_parameters"]["Parameters"] == "auto":
                for fric in ["mu", "k"]:
                    if inputSimFiles["entResInfo"][fric] == "Yes":
                        pathToFric, pathToFricFull, remeshedFric = dP.checkExtentAndCellSize(
                            cfgSim, inputSimFiles["%sFile" % fric], dem, fric
                        )
                        cfgSim["INPUT"]["%sFile" % fric] = pathToFric
                        inputSimFiles["entResInfo"]["%sRemeshed" % fric] = remeshedFric

            # check if forest effects = auto is chosen that forest parameter fields have correct extent
            if "res" in row._asdict()["simTypeList"] and inputSimFiles["resFile"] is not None:
                if (
                    cfgSim["FOREST_EFFECTS"]["Forest effects"] == "auto"
                    and inputSimFiles["entResInfo"]["bhd"] == "Yes"
                ):
                    pathToForest, pathToForestFull, remeshedForest = dP.checkExtentAndCellSize(
                        cfgSim, inputSimFiles["%sFile" % "bhd"], dem, "bhd"
                    )
                    cfgSim["INPUT"]["%sFile" % "bhd"] = pathToForest
                    inputSimFiles["entResInfo"]["%sRemeshed" % "bhd"] = remeshedForest

        # add info about entrainment file path to the cfg
        if "ent" in row._asdict()["simTypeList"] and inputSimFiles["entFile"] is not None:
            if inputSimFiles["entResInfo"]["entThFileType"] != ".shp":
                pathToEnt, pathToEntFull, remeshedEnt = dP.checkExtentAndCellSize(
                    cfgSim, inputSimFiles["entThFile"], dem, "ent"
                )
                cfgSim["INPUT"]["entThFile"] = pathToEnt
                inputSimFiles["entResInfo"]["entRemeshed"] = remeshedEnt
            cfgSim["INPUT"]["entrainmentScenario"] = str(pathlib.Path("ENT", inputSimFiles["entFile"].name))

        # add info about resistance file path to the cfg
        if "res" in row._asdict()["simTypeList"] and inputSimFiles["resFile"] is not None:
            if inputSimFiles["entResInfo"]["resFileType"] != ".shp":
                pathToRes, pathToResFull, remeshedRes = dP.checkExtentAndCellSize(
                    cfgSim, inputSimFiles["resFile"], dem, "res"
                )
                cfgSim["INPUT"]["resFile"] = pathToRes
                inputSimFiles["entResInfo"]["resRemeshed"] = remeshedRes
            cfgSim["INPUT"]["resistanceScenario"] = str(pathlib.Path("RES", inputSimFiles["resFile"].name))

        # add thickness values if read from shp and not varied
        cfgSim = dP.appendThicknessToCfg(cfgSim)

        # check differences to default and add indicator to name
        defID, _ = com1DFATools.compareSimCfgToDefaultCfgCom1DFA(cfgSim, module)

        # predefine different size classification indices
        frictIndi = None
        volIndi = None

        pathToDemFull = pathlib.Path(cfgSim["GENERAL"]["avalancheDir"], "Inputs", pathToDem)

        if modName in ["com1DFA", "com5SnowSlide", "com6RockAvalanche"]:
            # if frictModel is samosATAuto compute release vol
            if cfgSim["GENERAL"]["frictModel"].lower() == "samosatauto":
                relVolume = fetchRelVolume(
                    rel,
                    cfgSim,
                    pathToDemFull,
                    inputSimFiles["secondaryRelFile"],
                    timeDepRelFile=inputSimFiles["timeDepRelCsv"],
                )
            else:
                relVolume = ""

            # check sphKernelRadius setting
            cfgSim = checkCfg.checkCellSizeKernelRadius(cfgSim)

            # only keep friction model parameters that are used
            cfgSim = checkCfg.checkCfgFrictionModel(cfgSim, inputSimFiles, relVolume=relVolume)

            # set frictModelIndicator, this needs to happen AFTER checkCfgFrictModel
            frictIndi = com1DFATools.setFrictTypeIndicator(cfgSim)

        elif modName in ["com8MoTPSA", "com9MoTVoellmy"]:
            relVolume = fetchRelVolume(rel, cfgSim, pathToDemFull, inputSimFiles["secondaryRelFile"])

            # set Volume class identificator
            volIndi = setVolumeIndicator(cfgSim, relVolume)

        # convert back to configParser object
        cfgSimObject = cfgUtils.convertDictToConfigParser(cfgSim)
        # create unique hash for simulation configuration
        simHash = cfgUtils.cfgHash(cfgSimObject)

        simName = "_".join(
            filter(
                None,
                [
                    relNameSim,
                    simHash,
                    modNameShort,
                    defID,
                    frictIndi or volIndi,
                    row._asdict()["simTypeList"],
                    cfgSim["GENERAL"]["modelType"],
                ],
            )
        )

        # check if simulation exists. If yes do not append it
        if simName not in simNameExisting:
            simDict[simName] = {
                "simHash": simHash,
                "releaseScenario": relName,
                "simType": row._asdict()["simTypeList"],
                "relFile": rel,
                "cfgSim": cfgSimObject,
            }
            if modName in ["com1DFA", "com5SnowSlide", "com6RockAvalanche"]:
                # write configuration file, dont need to write cfg file for com8MoTPSA (does this later when creating rcf file)
                cfgUtils.writeCfgFile(
                    cfgSimObject["GENERAL"]["avalancheDir"],
                    com1DFA,
                    cfgSimObject,
                    fileName=simName,
                )
        else:
            log.warning("Simulation %s already exists, not repeating it" % simName)

    log.info("Done preparing variations -----")
    # TODO: maybe treat this in some other way, i.e. adding an "finalDEM" or similar
    inputSimFiles.pop("demFile")
    inputSimFiles["demFile"] = pathToDemFull

    return simDict

# override function
com1DFA.prepareVarSimDict = prepareVarSimDict

def c1TifMain(cfgMain, debrisCfg):
    """Run and adjust parameters to match debris flow settings for com1DFA run,
    result files, reports and plots are saved analog to a standard com1DFA model run

    Parameters
    -----------
    cfgMain: configparser object
        main DebrisFrame settings
    debrisCfg: configparser object
        configuration settings for debris flow including com1DFA override parameters

    """

    # ++++++++++ set configurations for com1DFA and override ++++++++++++
    # get comDFA configuration and update with debris flow parameter set
    com1DFACfg = cfgUtils.getModuleConfig(
        com1DFA,
        fileOverride="",
        modInfo=False,
        toPrint=False,
        onlyDefault=debrisCfg["com1DFA_com1DFA_override"].getboolean("defaultConfig"),
    )
    com1DFACfg, debrisCfg = cfgHandling.applyCfgOverride(
        com1DFACfg, debrisCfg, com1DFA, addModValues=False
    )

    # run the com1DFA module with debris flow settings
    dem, plotDict, reportDictList, simDF = com1DFA.com1DFAMain(
        cfgMain, cfgInfo=com1DFACfg
    )

    # print info about simulation performed to log
    log.info("Com1DFA run performed with debris flow settings")

    return dem, plotDict, reportDictList, simDF
