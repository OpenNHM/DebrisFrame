"""
    Pytest for module c1Ti
"""

#  Load modules
import configparser
import pathlib
import shutil
import pytest

from debrisframe.c1Ti import c1Ti

from avaframe.in3Utils import cfgUtils

def test_runC1Ti(tmp_path):
    """Check that runCom1DFA produces the good outputs"""

    testDir = pathlib.Path(__file__).parents[0]
    inputDir = testDir / "data" / "testC1Ti"
    avaDir = pathlib.Path(tmp_path, "testC1Ti")
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
    modCfg, modInfo = cfgUtils.getModuleConfig(c1Ti, modInfo=True)

    modCfg['com1DFA_com1DFA_override']['rho'] = '1000'
    modCfg['com1DFA_com1DFA_override']['explicitFriction'] = '0'
    modCfg['com1DFA_com1DFA_override']['frictModel'] = 'Voellmy'

    dem, plotDict, reportDictList, simDF = c1Ti.c1TiMain(cfgMain, modCfg)

    outDir = avaDir / "Outputs" / "com1DFA"
    for ext in ["pft", "pfv", "ppr"]:
        assert (outDir / "peakFiles" / ("%s_%s.asc" % (simDF["simName"].iloc[0], ext))).is_file()

    assert (outDir / "configurationFiles" / ("%s.ini" % (simDF["simName"].iloc[0]))).is_file()
    assert (outDir / "configurationFiles" / ("allConfigurations.csv")).is_file()
    assert simDF['rho'].iloc[0] == 1000
    assert simDF['explicitFriction'].iloc[0] == 0
    assert simDF['frictModel'].iloc[0] == 'Voellmy'
