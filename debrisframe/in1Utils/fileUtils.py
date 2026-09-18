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

    if inputsHydFile.exists():
        outputFileDF = pd.read_csv(outputFile)
        inputsHydFileDF = pd.read_csv(inputsHydFile)

        if outputFileDF.equals(inputsHydFileDF):
            log.info(f"{inputsHydFile} already exists and is consistent with {outputFile}")
        else:
            message = f"""{inputsHydFile} already exists and is inconsistent with {outputFile}.
            {inputsHydFile} is overwritten by {outputFile}!"""
            log.info(message)
            shutil.copy2(outputFile, inputsHydFile)

    shutil.copy2(outputFile, inputsHydFile)
