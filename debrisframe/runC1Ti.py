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
# from debrisframe.como1Debris import como1Debris
from c1Ti import c1Ti


def runC1Ti(debrisDir=""):
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
    logName = "runComo1Debris"

    # Load debris flow directory from general configuration file
    # More information about the configuration can be found here
    # on the Configuration page in the documentation
    cfgMain = cfgUtils.getGeneralConfig(nameFile=pathlib.Path("debrisframeCfg.ini"))
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
    DebrisCfg = cfgUtils.getModuleConfig(c1Ti)

    # perform com1DFA simulation with debris flow settings
    _, plotDict, reportDictList, _ = c1Ti.c1TiMain(cfgMain, DebrisCfg)

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
    runC1Ti(str(args.debrisdir))
