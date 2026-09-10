"""
Run the In2TopoHyd module to get the initial conditions at the release line
"""

# load modules
import time
import pathlib
import argparse

# local imports
from avaframe.in3Utils import cfgUtils
from avaframe.in3Utils import logUtils

# import computation modules
import debrisframe as debf
from debrisframe.in2TopoHyd import in2TopoHyd


def runIn2TopoHyd(debrisDir=""):
    """
    Run in2TopoHyd with only a debris flow directory as input

    Parameters
    ----------
    debrisDir: str
        path to debris flow directory (setup e.g. with init scripts)

    Returns
    -------
    csv-file with initial conditions at the release line
    Plots of cross section and rating curve
    cross-section cell centers as csv-file - optional
    """

    # Time the whole routine
    startTime = time.time()

    # log file name; leave empty to use default runLog.log
    logName = "runIn2TopoHyd"

    # Load debris flow directory from general configuration file
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

    # load module config
    # topoHydCfg
    topoHydCfg = cfgUtils.getModuleConfig(in2TopoHyd, debrisDir, toPrint=False)

    # ----------------
    # Run in2TopoHyd
    in2TopoHyd.in2TopoHydMain(debrisDir, topoHydCfg)

    # Print time needed
    endTime = time.time()
    log.info("Took %6.1f seconds to calculate." % (endTime - startTime))

    return


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

    args = parser.parse_args()
    runIn2TopoHyd(str(args.debrisdir))
