"""
Pytest for module c1TIF
"""

#  Load modules
import configparser
import pathlib
import shutil
import pytest

from debrisframe.c1TIF import c1TIF
from debrisframe import runC1TIF
from debrisframe import runIn2DFHyd
from debrisframe.in1Utils import fileUtils

from avaframe.in3Utils import cfgUtils


def test_runC1TIF(tmp_path):
    """Check that runC1TIF produces the good outputs"""

    testDir = pathlib.Path(__file__).parents[1]
    inputDir = testDir / "data" / "debrisParabolaChanneled"
    avaDir = pathlib.Path(tmp_path, "testC1TIF")
    shutil.copytree(inputDir, avaDir, ignore=shutil.ignore_patterns("Work", "Outputs"))

    cfgMain = configparser.ConfigParser()
    cfgMain["MAIN"] = {"avalancheDir": str(avaDir), "nCPU": "auto", "CPUPercent": "90"}
    cfgMain["FLAGS"] = {
        "showPlot": "False",
        "savePlot": "True",
        "ReportDir": "True",
        "reportOneFile": "True",
        "debugPlot": "False",
    }

    modCfg, modInfo = cfgUtils.getModuleConfig(c1TIF, modInfo=True, onlyDefault=True)

    modCfg["com1DFA_com1DFA_override"]["rho"] = "2000"
    modCfg["com1DFA_com1DFA_override"]["explicitFriction"] = "0"
    modCfg["com1DFA_com1DFA_override"]["frictModel"] = "Voellmy"

    runIn2DFHyd.runIn2DFHyd(str(avaDir))
    fileUtils.copyHydrToInput(avaDir)

    dem, plotDict, reportDictList, simDF = c1TIF.c1TIFMain(cfgMain, modCfg)

    outDir = avaDir / "Outputs" / "com1DFA"
    for ext in ["pft", "pfv", "ppr"]:
        assert (outDir / "peakFiles" / ("%s_%s.asc" % (simDF["simName"].iloc[0], ext))).is_file()

    assert (outDir / "configurationFiles" / ("%s.ini" % (simDF["simName"].iloc[0]))).is_file()
    assert (outDir / "configurationFiles" / ("allConfigurations.csv")).is_file()
    assert simDF["rho"].iloc[0] == 2000
    assert simDF["explicitFriction"].iloc[0] == 0
    assert simDF["frictModel"].iloc[0] == "Voellmy"


def test_runC1TIF_expertCfg(tmp_path):
    """Expert Inputs/CFGs/c1TIFCfg.ini must take effect in runC1TIF"""

    testDir = pathlib.Path(__file__).parents[1]
    inputDir = testDir / "data" / "debrisParabolaChanneled"
    avaDir = pathlib.Path(tmp_path, "testC1TIF")
    shutil.copytree(inputDir, avaDir, ignore=shutil.ignore_patterns("Work", "Outputs"))

    cfgDir = avaDir / "Inputs" / "CFGs"
    cfgDir.mkdir(parents=True)
    expertCfg = cfgDir / "c1TIFCfg.ini"
    expertCfg.write_text("[com1DFA_com1DFA_override]\nrho = 3000\n")

    runIn2DFHyd.runIn2DFHyd(str(avaDir))
    fileUtils.copyHydrToInput(avaDir)

    runC1TIF.runC1TIF(str(avaDir))

    # expert config survives cleanSingleAvaDir (Review Focus 4)
    assert expertCfg.is_file()
    # override was read from Inputs/CFGs, not the packaged default (Review Focus 1, 5)
    simDF, _ = cfgUtils.readAllConfigurationInfo(str(avaDir))
    assert int(simDF["rho"].iloc[0]) == 3000
