"""
Directory and file handling helper functions
"""

import pathlib
import shutil
import logging
import pandas as pd

from avaframe.in1Data import getInput as gI

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

    # in2TopoHyd names its output csv-file after the release-line shapefile in Inputs/XSECT
    xsectFile, *_ = gI.getAndCheckInputFiles(
        inputDir=debrisDir / "Inputs", folder="XSECT", inputType="Release line"
    )
    if xsectFile is None:
        message = "No Release line shp-file in Inputs/XSECT!"
        log.error(message)
        raise FileNotFoundError(message)
    outputName = pathlib.Path(xsectFile).stem

    outputFile = debrisDir / "Outputs" / "in2TopoHyd" / f"{outputName}.csv"
    inputsDir = debrisDir / "Inputs" / "REL"
    inputsDir.mkdir(parents=True, exist_ok=True)

    inputsHydFile = inputsDir / outputFile.name

    if not inputsHydFile.exists():
        shutil.copy2(outputFile, inputsHydFile)
        log.info(
            f"c1TIF simulation input file derived from debris-flow hydrograph is saved to {inputsHydFile}"
        )
    else:
        outputFileDF = pd.read_csv(outputFile)
        inputsHydFileDF = pd.read_csv(inputsHydFile)

        if not outputFileDF.equals(inputsHydFileDF):
            log.info(f"{inputsHydFile} already exists and is inconsistent with {outputFile}.")
            log.info(f"{inputsHydFile} is overwritten by {outputFile}!")
            shutil.copy2(outputFile, inputsHydFile)
        else:
            log.info(f"{inputsHydFile} already exists and is consistent with {outputFile}")
