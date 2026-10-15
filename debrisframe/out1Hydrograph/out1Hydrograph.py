"""
Export coordinates of cross section cells to csv-file for plotting output hydrographs
"""

# load modules
import logging
import pandas as pd
import pathlib

# local imports
from avaframe.in3Utils import geoTrans
import avaframe.in3Utils.fileHandlerUtils as fU

import debrisframe.in2TopoHyd.in2TopoHyd as inTopHyd

# create local logger under avaframe namespace to use its logging configuration
log = logging.getLogger("avaframe.debrisframe.out1Hydrograph")


def out1HydrographMain(debrisDir, debrisCfg):

    # get output hydrograph output lines
    inputDir = pathlib.Path(debrisDir, "Inputs")
    dem = inTopHyd.getDEMRaster(debrisDir, debrisCfg)
    outLine = inTopHyd.getInputShapeFiles(
        inputDir=inputDir, folder="OUTHYDR", fileType="Output hydrograph", dem=dem, idField="Station"
    )

    # get cross section cells for every hydrograph output line
    outputCrossSection = {}
    for i, id in enumerate(outLine["ID"]):
        start = int(outLine["Start"][i])
        end = start + int(outLine["Length"][i])

        # Create a dictionary for the current hydrograph line
        singleLine = {
            "x": outLine["x"][start:end],
            "y": outLine["y"][start:end],
        }
        # get cross section cells
        crossSection = inTopHyd.getCrossSectionCells(dem, singleLine)
        crossSection = geoTrans.computeS(crossSection)

        outputCrossSection[str(id)] = crossSection

    # export to csv-file
    station = []
    row = []
    col = []
    dist = []
    x = []
    y = []

    for xs in outputCrossSection.keys():
        for j in range(len(outputCrossSection[xs]["x"])):
            station.append(xs)
            row.append(outputCrossSection[xs]["crossSectIdx"][0][j])
            col.append(outputCrossSection[xs]["crossSectIdx"][1][j])
            dist.append(outputCrossSection[xs]["s"][j])
            x.append(outputCrossSection[xs]["x"][j])
            y.append(outputCrossSection[xs]["y"][j])

    outputCrossSection = pd.DataFrame(
        {
            "station": station,
            "row": row,
            "column": col,
            "distance": dist,
        }
    )

    # create output directory
    outputDir = pathlib.Path(debrisDir, "Inputs", "OUTHYDR", "outputCrossSection.csv")
    # write csv-file
    outputCrossSection.to_csv(outputDir, sep=",", decimal=".", header=True, index=False)

    # create data frame with cell coordinates along output cross sections - for plausability checks
    outputCoords = pd.DataFrame({"station": station, "x": x, "y": y})
    # create output directory
    outputDir = pathlib.Path(debrisDir, "Outputs", "out1Hydrograph")
    fU.makeADir(outputDir)
    # write csv-file
    outputCoords.to_csv(outputDir / "outputCoordinates.csv", sep=",", decimal=".", header=True, index=False)
