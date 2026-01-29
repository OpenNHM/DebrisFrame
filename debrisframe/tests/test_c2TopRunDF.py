"""
Pytest for module c2TopRunDF
"""

#  Load modules
import configparser
import pathlib
import shutil
import pytest
import numpy as np
import avaframe.in2Trans.rasterUtils as rasterUtils

from debrisframe.c2TopRunDF import c2TopRunDF


def test_runC2TopRunDF(tmp_path):
    """Check that runCom1DFA produces the good outputs"""

    testDir = pathlib.Path(__file__).parents[0]
    refDir = testDir / "data" / "testC2TopRunDF" / "Reference" / "depo.asc"
    debDir = pathlib.Path(__file__).parents[1]

    inputDir = debDir / "data" / "debrisTopRun"
    avaDir = pathlib.Path(tmp_path, "debrisTopRun")
    shutil.copytree(inputDir, avaDir)

    cfgMain = configparser.ConfigParser()
    cfgMain["MAIN"] = {"avalancheDir": str(avaDir), "nCPU": "auto", "CPUPercent": "90"}
    cfgMain["FLAGS"] = {
        "showPlot": "False",
        "savePlot": "True",
        "ReportDir": "True",
        "reportOneFile": "True",
        "debugPlot": "False",
    }
    # modCfg, modInfo = cfgUtils.getModuleConfig(com1DFA, fileOverride=cfgFile, modInfo=True)

    cfg = configparser.ConfigParser()
    cfg["GENERAL"] = {
        "name": "Scenario1",
        "xKoord": "660926",
        "yKoord": "151744",
        "energyHeight": "0.1",
        "volume": "4000",
        "coefficient": "28",
    }
    # To get a reproduceable result, set the seed as in the test case:
    np.random.seed(42)

    c2TopRunDF.c2TopRunDFMain(cfgMain, cfg)

    outDir = avaDir / "Outputs" / "c2TopRunDF"
    outputfile = outDir / "depo.asc"

    refData = rasterUtils.readRaster(refDir)
    outData = rasterUtils.readRaster(outputfile)

    assert outputfile.is_file()
    assert np.all(np.isclose(refData["rasterData"], outData["rasterData"]))
    for headerVariable in ["ncols", "nrows", "xllcenter", "cellsize"]:
        assert refData["header"][headerVariable] == outData["header"][headerVariable]
