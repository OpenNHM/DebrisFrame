import pathlib
import time
import argparse

# Local imports
# import config and init tools
from avaframe.in3Utils import cfgUtils
from avaframe.in3Utils import logUtils
import avaframe.in3Utils.initializeProject as initProj

import debrisframe as debf
from debrisframe.c2TopRunDF import c2TopRunDF

def runC2TopRunDF(debrisDir="", xCoordRel=None, yCoordRel=None):

    # Time the whole routine
    startTime = time.time()

    # log file name; leave empty to use default runLog.log
    logName = "runC2TopRunDF"

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

    initProj.cleanSingleAvaDir(debrisDir, deleteOutput=False)
    DebrisCfg = cfgUtils.getModuleConfig(c2TopRunDF)

    # get release coordinates if provided from a point
    if xCoordRel is not None:
        DebrisCfg["GENERAL"]["xKoord"] = xCoordRel
    if yCoordRel is not None:
        DebrisCfg["GENERAL"]["yKoord"] = yCoordRel

    c2TopRunDF.c2TopRunDFMain(cfgMain, DebrisCfg)

    endTime = time.time()
    log.info("Took %6.1f seconds to calculate." % (endTime - startTime))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run debris flow workflow")
    parser.add_argument(
        "debrisdir",
        metavar="debrisdir",
        type=str,
        nargs="?",
        default="",
        help="the debris directory",
    )
    parser.add_argument(
        "-x",
        "--release_Xcoordinate",
        type=str,
        help="x coordinate of release point" + "Overrides default AND local configs",
    )
    parser.add_argument(
        "-y",
        "--release_Ycoordinate",
        type=str,
        help="y coordinate of release point" + "Overrides default AND local configs",
    )
    args = parser.parse_args()
    runC2TopRunDF(str(args.debrisdir), args.release_Xcoordinate, args.release_Ycoordinate)
