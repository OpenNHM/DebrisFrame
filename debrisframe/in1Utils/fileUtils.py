"""
Directory and file handling helper functions
"""

import pathlib
import shutil
import logging

log = logging.getLogger("avaframe.debrisframe.in1Utils.fileUtils")


def copyHydrToInput(debrisDir):
    """
    copy the output file from in2TopoHyd into Inputs/REL
    to serve as input data for c1TIF

    Parameters
    -----------
    debrisDir: str or pathlib path
        path to debris-flow directory
    """

    debrisDir = pathlib.Path(debrisDir)

    outputFile = debrisDir / "Outputs" / "in2TopoHyd" / "initCondHyd.csv"
    inputsDir = debrisDir / "Inputs" / "REL"
    inputsDir.mkdir(parents=True, exist_ok=True)

    inputsHydFile = inputsDir / outputFile.name

    # TODO: How should we handle if the file already exists?
    if inputsHydFile.exists():
        raise FileExistsError(f"File already exists: {inputsHydFile}")

    shutil.copy2(outputFile, inputsHydFile)
