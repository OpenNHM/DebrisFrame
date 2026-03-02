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
import avaframe.in3Utils.initializeProject as initProj
from avaframe.in3Utils import fileHandlerUtils as fU

# import computation modules
import debrisframe as debf
from debrisframe.c1Tif import c1Tif


def runC1Tif(debrisDir=""):
    """Run com1DFA with debris flow parameters with only an avalanche/ debris flow directory as input

    Parameters
    ----------
    debrisDir: str
        path to debris flow directory (setup e.g. with init scripts)

    Returns
    -------
    peakFilesDF: pandas dataframe
        with info about com1DFA peak file locations
    """
    # Time the whole routine
    startTime = time.time()

    # log file name; leave empty to use default runLog.log
    logName = "runC1Tif"

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
    DebrisCfg = cfgUtils.getModuleConfig(c1Tif)

    # perform com1DFA simulation with debris flow settings
    _, plotDict, reportDictList, _ = c1Tif.c1TifMain(cfgMain, DebrisCfg)

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
    print(parser)
    args = parser.parse_args()
    runC1Tif(str(args.debrisdir))
