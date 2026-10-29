"""
Export coordinates of cross section cells to csv-file for plotting output hydrographs
"""

# load modules
import logging
import pandas as pd
import pathlib
import numpy as np

# local imports
from avaframe.in3Utils import geoTrans
import avaframe.in3Utils.fileHandlerUtils as fU
import avaframe.com1DFA.DFAtools as DFAtls

import debrisframe.in2TopoHyd.in2TopoHyd as inTopHyd

# create local logger under avaframe namespace to use its logging configuration
log = logging.getLogger("avaframe.debrisframe.out1Hydrograph")


def projectCellCenterToLine(outputLine, crossSectionCells):

    # get starting and ending points of line
    xcoordStart = outputLine["x"][0]
    ycoordStart = outputLine["y"][0]
    xcoordEnd = outputLine["x"][1]
    ycoordEnd = outputLine["y"][1]
    lineStart = np.array([xcoordStart, ycoordStart])
    lineEnd = np.array([xcoordEnd, ycoordEnd])

    # get coordinates of cell centers
    cllCtreX = crossSectionCells["x"]
    cllCtreY = crossSectionCells["y"]
    cellCenters = np.stack((cllCtreX, cllCtreY), axis=1)

    # get direction of line
    lineDir = lineEnd - lineStart
    lineLengthSqrt = np.dot(lineDir, lineDir)

    if lineLengthSqrt == 0:
        raise ValueError("The line starting and ending points must differ!")

    # Orthogonal projection onto the line segment
    t = np.dot(cellCenters - lineStart, lineDir) / lineLengthSqrt
    t = np.clip(t, 0.0, 1.0)
    projectedCenters = lineStart + t[:, np.newaxis] * lineDir
    projCtreX = projectedCenters[:, 0]
    projCtreY = projectedCenters[:, 1]

    # Distances between consecutive projected points
    distances = np.hypot(np.diff(projCtreX), np.diff(projCtreY))

    return projCtreX, projCtreY, distances


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
        projCtreX, projCtreY, distances = projectCellCenterToLine(singleLine, crossSection)

        outputCrossSection[str(id)] = crossSection
        outputCrossSection[str(id)]["prjCtreX"] = projCtreX
        outputCrossSection[str(id)]["prjCtreY"] = projCtreY

        # get starting and ending points of cross section
        xcoordStart = crossSection["x"][0]
        ycoordStart = crossSection["y"][0]
        xcoordEnd = crossSection["x"][-1]
        ycoordEnd = crossSection["y"][-1]

        # get direction of cross section
        dx = xcoordEnd - xcoordStart
        dy = ycoordEnd - ycoordStart

        # calculate unit normal vectors on left- and right side
        # of direction vector
        nx1, ny1, _ = DFAtls.normalize(-dy, dx, 0)
        nx2, ny2, _ = DFAtls.normalize(dy, -dx, 0)

        # store vectors
        outputCrossSection[str(id)]["Nx1"] = nx1
        outputCrossSection[str(id)]["Nx2"] = nx2
        outputCrossSection[str(id)]["Ny1"] = ny1
        outputCrossSection[str(id)]["Ny2"] = ny2

    # export to csv-file
    station = []
    row = []
    col = []
    x = []
    y = []
    nx1 = []
    nx2 = []
    ny1 = []
    ny2 = []
    prjX = []
    prjY = []

    for xs in outputCrossSection.keys():
        for j in range(len(outputCrossSection[xs]["x"])):
            station.append(xs)
            nx1.append(outputCrossSection[xs]["Nx1"])
            nx2.append(outputCrossSection[xs]["Nx2"])
            ny1.append(outputCrossSection[xs]["Ny1"])
            ny2.append(outputCrossSection[xs]["Ny2"])
            row.append(outputCrossSection[xs]["crossSectIdx"][0][j])
            col.append(outputCrossSection[xs]["crossSectIdx"][1][j])
            x.append(outputCrossSection[xs]["x"][j])
            y.append(outputCrossSection[xs]["y"][j])
            prjX.append(outputCrossSection[xs]["prjCtreX"][j])
            prjY.append(outputCrossSection[xs]["prjCtreY"][j])

    outputCrossSection = pd.DataFrame(
        {
            "station": station,
            "row": row,
            "column": col,
            "Nx1": nx1,
            "Ny1": ny1,
            "Nx2": nx2,
            "Ny2": ny2,
        }
    )

    # create output directory
    outputDir = pathlib.Path(debrisDir, "Inputs", "OUTHYDR", "outputCrossSection.csv")
    # write csv-file
    outputCrossSection.to_csv(outputDir, sep=",", decimal=".", header=True, index=False)

    # create data frame with cell coordinates along output cross sections - for plausability checks
    outputCoords = pd.DataFrame({"station": station, "x": x, "y": y, "projCtreX": prjX, "projCtreY": prjY})
    # create output directory
    outputDir = pathlib.Path(debrisDir, "Outputs", "out1Hydrograph")
    fU.makeADir(outputDir)
    # write csv-file
    outputCoords.to_csv(outputDir / "outputCoordinates.csv", sep=",", decimal=".", header=True, index=False)
