"""
Export coordinates of cross section cells to csv-file for plotting output hydrographs
"""

# load modules
import logging
import pandas as pd
import pathlib
import numpy as np

# local imports
import avaframe.in3Utils.fileHandlerUtils as fU
import avaframe.com1DFA.DFAtools as DFAtls

import debrisframe.in2DFHyd.in2DFHyd as inDFHyd

# create local logger under avaframe namespace to use its logging configuration
log = logging.getLogger("avaframe.debrisframe.out1HelpHyd")


def projectCellCenterToLine(outputLine, crossSectionCells):
    """
    Projects the coordinates of the cross-section cell centers
    onto the cross-section line

    Parameters
    -----------
    outputLine: dict
        dictionary with x- and y-coordinates of the starting and ending point
        of the cross-section line
    crossSectionCells: dict
        dictionary with x- and y-coordinates of the cross-section cell centers

    Returns
    --------
    projCtreX: 1D-array
        projected x-coordinates
    projCtreY: 1D-array
            projected y-coordinates
    projCsz: 1D-array
        projected cell size
    """

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
    d = np.hypot(np.diff(projCtreX), np.diff(projCtreY))
    # half distance between neighbouring points -> cell size for arbitrary orientation of cross-section line
    projCsz = np.empty_like(projCtreX)
    projCsz[1:-1] = 0.5 * (d[:-1] + d[1:])
    projCsz[0] = 0.5 * d[0]
    projCsz[-1] = 0.5 * d[-1]

    return projCtreX, projCtreY, projCsz


def out1HelpDFHydMain(debrisDir, debrisCfg):
    """
    Main script to run the out1HelpDFHyd module

    Parameters
    -----------
    debrisDir: str or pathlib path
        path to debris-flow directory
    debrisCfg: configparser.ConfigParser
            configuration file for the c1TIF-module

    Returns
    --------
    csv-file with station name, indices, normal vectors and projected cell sizes
    of the output cross-section lines
    csv-file with the coordinates of the output cross-section lines and projected points
    """

    # get output hydrograph output lines
    inputDir = pathlib.Path(debrisDir, "Inputs")
    dem = inDFHyd.getDEMRaster(debrisDir, debrisCfg)
    outLine = inDFHyd.getInputShapeFiles(
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
        crossSection = inDFHyd.getCrossSectionCells(dem, singleLine)
        projCtreX, projCtreY, projCsz = projectCellCenterToLine(singleLine, crossSection)

        outputCrossSection[str(id)] = crossSection
        outputCrossSection[str(id)]["prjCtreX"] = projCtreX
        outputCrossSection[str(id)]["prjCtreY"] = projCtreY
        outputCrossSection[str(id)]["prjCsz"] = projCsz

        # get starting and ending points of cross section
        xcoordStart = crossSection["x"][0]
        ycoordStart = crossSection["y"][0]
        xcoordEnd = crossSection["x"][-1]
        ycoordEnd = crossSection["y"][-1]

        # get direction of cross section
        dx = xcoordEnd - xcoordStart
        dy = ycoordEnd - ycoordStart

        # calculate unit normal vector
        nx, ny, _ = DFAtls.normalize(-dy, dx, 0)

        # store vectors
        outputCrossSection[str(id)]["Nx"] = nx
        outputCrossSection[str(id)]["Ny"] = ny

    # export to csv-file
    station = []
    row = []
    col = []
    x = []
    y = []
    nx = []
    ny = []
    prjX = []
    prjY = []
    prjCellSize = []

    for xs in outputCrossSection.keys():
        for j in range(len(outputCrossSection[xs]["x"])):
            station.append(xs)
            nx.append(outputCrossSection[xs]["Nx"])
            ny.append(outputCrossSection[xs]["Ny"])
            row.append(outputCrossSection[xs]["crossSectIdx"][0][j])
            col.append(outputCrossSection[xs]["crossSectIdx"][1][j])
            x.append(outputCrossSection[xs]["x"][j])
            y.append(outputCrossSection[xs]["y"][j])
            prjX.append(outputCrossSection[xs]["prjCtreX"][j])
            prjY.append(outputCrossSection[xs]["prjCtreY"][j])
            prjCellSize.append(outputCrossSection[xs]["prjCsz"][j])

    outputCrossSection = pd.DataFrame(
        {
            "station": station,
            "row": row,
            "column": col,
            "Nx": nx,
            "Ny": ny,
            "prjCsz": prjCellSize,
        }
    )

    # create output directory
    outputDir = pathlib.Path(debrisDir, "Inputs", "OUTHYDR", "outputCrossSection.csv")
    # write csv-file
    outputCrossSection.to_csv(outputDir, sep=",", decimal=".", header=True, index=False)

    # create data frame with cell coordinates along output cross sections - for plausability checks
    outputCoords = pd.DataFrame({"station": station, "x": x, "y": y, "projCtreX": prjX, "projCtreY": prjY})
    # create output directory
    outputDir = pathlib.Path(debrisDir, "Outputs", "out1HelpDFHyd")
    fU.makeADir(outputDir)
    # write csv-file
    outputCoords.to_csv(outputDir / "outputCoordinates.csv", sep=",", decimal=".", header=True, index=False)
