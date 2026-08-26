"""
Run the debris flow setup of com1DFA
"""

import pathlib
import time
import argparse

# Local imports
# import config and init tools
from avaframe.in3Utils import cfgUtils
from avaframe.in3Utils import logUtils
from avaframe.in3Utils import cfgHandling
import avaframe.in3Utils.initializeProject as initProj
from avaframe.in3Utils import fileHandlerUtils as fU

# import computation modules
import debrisframe as debf
from debrisframe.c1TIF import c1TIF
from debrisframe.in2TopoHyd import in2TopoHyd
from debrisframe.in1Utils import fileUtils


def runC1TIF(debrisDir="", inHydr=False):
    """Run com1DFA with debris flow parameters with only an avalanche/ debris flow directory as input

    Parameters
    ----------
    debrisDir: str
        path to debris flow directory (setup e.g. with init scripts)
    inHydr: bool
        if inHydr is True, the initial conditions for c1TIF
        are computed from a hydrograph first by executing in2TopoHyd

    Returns
    -------
    peakFilesDF: pandas dataframe
        with info about com1DFA peak file locations
    """
    # Time the whole routine
    startTime = time.time()

    # log file name; leave empty to use default runLog.log
    logName = "runC1TIF"

    # Load debris flow directory from general configuration file
    # More information about the configuration can be found here
    # on the Configuration page in the documentation
    modPath = pathlib.Path(debf.__file__).resolve().parent
    cfgNameFile = modPath / "debrisframeCfg.ini"
    cfgMain = cfgUtils.getGeneralConfig(nameFile=cfgNameFile)
    if debrisDir != "":
        cfgMain["MAIN"]["avalancheDir"] = debrisDir
        # TODO: change avalancheDir to debrisDir
    else:
        debrisDir = cfgMain["MAIN"]["avalancheDir"]

    # Start logging
    log = logUtils.initiateLogger(debrisDir, logName)
    log.info("MAIN SCRIPT")
    log.info("Current debris flow: %s", debrisDir)

    # ----------------
    # Clean input directory(ies) of old work files
    initProj.cleanSingleAvaDir(debrisDir, deleteOutput=False)

    # load debris flow config
    DebrisCfg = cfgUtils.getModuleConfig(c1TIF)

    # ---------------------
    # check if in2TopoHyd computes input data for c1TIF
    # TODO: should we also override the flag, in Expert mode?
    if inHydr:
        DebrisCfg["GENERAL"]["inputHydrograph"] = "True"
    else:
        inHydr = DebrisCfg["GENERAL"].getboolean("inputHydrograph")

    if inHydr:
        # TODO: put this in an separate function? -> where?
        if DebrisCfg["com1DFA_com1DFA_override"].getboolean("timeDependentRelease") is False:
            message = "If input data are computed from hydrograph, timeDependentRelease needs to be set to True."
            log.error(message)
            raise ValueError(message)

        in2TopoHydCfg = cfgUtils.getModuleConfig(
            in2TopoHyd,
            fileOverride="",
            modInfo=False,
            toPrint=False,
            onlyDefault=DebrisCfg["in2TopoHyd_in2TopoHyd_override"].getboolean("defaultConfig"),
        )
        in2TopoHydCfg, debrisCfg = cfgHandling.applyCfgOverride(
            in2TopoHydCfg, DebrisCfg, in2TopoHyd, addModValues=False
        )

        in2TopoHyd.in2TopoHydMain(debrisDir, in2TopoHydCfg, DebrisCfg)

        # copy in2TopoHyd output into Inputs folder for c1TIF
        fileUtils.copyHydrToInput(debrisDir)

    # perform com1DFA simulation with debris flow settings
    _, plotDict, reportDictList, _ = c1TIF.c1TIFMain(cfgMain, DebrisCfg)

    # Get peakfiles to return to QGIS
    debrisDir = pathlib.Path(debrisDir)
    inputDir = debrisDir / "Outputs" / "com1DFA" / "peakFiles"
    peakFilesDF = fU.makeSimDF(inputDir, avaDir=debrisDir)

    # Print time needed
    endTime = time.time()
    log.info("Took %6.1f seconds to calculate." % (endTime - startTime))

    return peakFilesDF


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run debris flow workflow")
    parser.add_argument(
        "debrisdir",
        metavar="debrisdir",
        type=str,
        nargs="?",
        default="",
        help="the avalanche/ debris directory",
    )
    parser.add_argument(
        "-inHydr",
        "--inputHydrograph",
        action="store_true",
        help="If set, input data is computed from a hydrograph. "
             + "If omitted, the default/ini configuration is used."
    )
    args = parser.parse_args()
    runC1TIF(str(args.debrisdir), args.inputHydrograph)
