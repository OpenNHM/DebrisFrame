"""
Pytest for module in1Utils.fileUtils
"""

import os

import pandas as pd

from debrisframe.in1Utils import fileUtils


def _writeHydFile(path, flowArea):
    pd.DataFrame({"flowArea": flowArea}).to_csv(path, index=False)


def test_copyHydrToInput_doesNotOverwriteConsistentFile(tmp_path):
    """Check that an already consistent Inputs/REL hydrograph is left untouched."""
    debrisDir = tmp_path / "avaDir"
    outputFile = debrisDir / "Outputs" / "in2TopoHyd" / "initCondHyd.csv"
    inputsHydFile = debrisDir / "Inputs" / "REL" / "initCondHyd.csv"
    outputFile.parent.mkdir(parents=True)
    inputsHydFile.parent.mkdir(parents=True)

    flowArea = [1.0, 2.0, 3.0]
    _writeHydFile(outputFile, flowArea)
    _writeHydFile(inputsHydFile, flowArea)

    # mark the existing input file with a distinctive modification time
    oldTime = 1000000000
    os.utime(inputsHydFile, (oldTime, oldTime))

    fileUtils.copyHydrToInput(debrisDir)

    assert inputsHydFile.stat().st_mtime == oldTime
