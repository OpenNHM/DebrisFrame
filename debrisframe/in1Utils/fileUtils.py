"""
Directory and file handling helper functions
"""

import pathlib
import shutil
import logging
import pandas as pd

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

    if not inputsHydFile.exists():
        shutil.copy2(outputFile, inputsHydFile)
    else:
        outputFileDF = pd.read_csv(outputFile)
        inputsHydFileDF = pd.read_csv(inputsHydFile)

        if not outputFileDF.equals(inputsHydFileDF):
            log.info(f"{inputsHydFile} already exists and is inconsistent with {outputFile}.")
            log.info(f"{inputsHydFile} is overwritten by {outputFile}!")
            shutil.copy2(outputFile, inputsHydFile)
        else:
            log.info(f"{inputsHydFile} already exists and is consistent with {outputFile}")
