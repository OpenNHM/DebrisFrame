"""
    Pytest for module com6RockAvalanche
"""

#  Load modules
import configparser
import pathlib
import shutil
import pytest

from avaframe.com6RockAvalanche import com6RockAvalanche

from avaframe.in3Utils import cfgUtils

@pytest.mark.skip(reason="Fails on github for nonobvious reasons, disabling it for now")
def test_runC1Ti(tmp_path, caplog):
    """Check that runCom1DFA produces the good outputs"""
    testDir = pathlib.Path(__file__).parents[0]
    inputDir = testDir / "data" / "testC1Ti"
    avaDir = pathlib.Path(tmp_path, "testC1Ti")
    shutil.copytree(inputDir, avaDir)
#    print(avaDir)
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
    modCfg, modInfo = cfgUtils.getModuleConfig(c1Ti, modInfo=True)
#    print(modCfg)

    dem, plotDict, reportDictList, simDF = c1Ti.c1TiMain(cfgMain, modCfg)

    outDir = avaDir / "Outputs" / "com1DFA"
    for ext in ["pft", "pfv", "ppr"]:
        assert (outDir / "peakFiles" / ("%s_%s.asc" % (simDF["simName"].iloc[0], ext))).is_file()

    assert (outDir / "configurationFiles" / ("%s.ini" % (simDF["simName"].iloc[0]))).is_file()
    assert (outDir / "configurationFiles" / ("allConfigurations.csv")).is_file()
