"""
Get initial conditions for hydrograph
"""

# Load modules
import pathlib
import math
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# local imports
from avaframe.in1Data import getInput as gI
from avaframe.in3Utils import geoTrans
import avaframe.in2Trans.shpConversion as shpConv
import avaframe.com1DFA.DFAtools as DFAtls
import avaframe.in3Utils.fileHandlerUtils as fU

# create local logger under avaframe namespace to use its logging configuration
log = logging.getLogger("avaframe.debrisframe.in2TopoHyd")


def assignCrossSectionCoords(leveePoints, crossSection):
    """
    Assign the nearest cross-section coordinates to the levee points

    Parameters
    -----------
    leveePoints: dict
        dictionary containing x,y-coordinates of levee points
    crossSection: dict
        dictionary containing x,y-coordinates of cross-section cells

    Returns
    --------
    crossSection: dict
        see input parameter
        additional levee information about x,y-coordinates,
        elevation, distance and indices projected on nearest
        cross-section cell
    """
    # assign levee points to cross section cells
    xcoordLevee = leveePoints["x"]
    ycoordLevee = leveePoints["y"]

    idPoint = []
    for x, y in zip(xcoordLevee, ycoordLevee):
        diffX = crossSection["x"] - x
        diffY = crossSection["y"] - y
        dist = np.sqrt(diffX * diffX + diffY * diffY)
        id = min(dist)
        id = np.where(dist == id)
        idPoint.append(id[0][0])

    xLevee = crossSection["x"][idPoint]
    yLevee = crossSection["y"][idPoint]
    elevLevee = crossSection["elevation"][idPoint]
    sLevee = crossSection["s"][idPoint]

    if np.min(sLevee) == 0.0 or np.max(sLevee) == crossSection["s"][-1]:
        message = """At least one levee point lies on the starting or ending point of your release line!
            Ensure that you keep a distance of at least one raster cell interior to the edges"""
        log.error(message)
        raise IndexError(message)

    crossSection["idLevee"] = idPoint
    crossSection["xLevee"] = xLevee
    crossSection["yLevee"] = yLevee
    crossSection["elevLevee"] = elevLevee
    crossSection["sLevee"] = sLevee

    return crossSection


def assignRasterCoords(cellSize, releaseLine):
    """
    Assign nearest raster coordinates to the release line

    Parameters
    -----------
    cellSize: int
        dem cell size
    releaseLine: dict
        dictionary including starting and ending point of release line

    Returns
    --------
    releaseLine: dict
        dictionary including new coordinates for start and ending point
    """

    # assign raster cell coord to starting and ending point of release line
    xcoord = []
    ycoord = []
    for x, y in zip(releaseLine["x"], releaseLine["y"]):
        dx = x % cellSize
        dy = y % cellSize
        if dx < cellSize / 2:
            xcoord.append(x - x % cellSize)
        else:
            xcoord.append(x + (cellSize - x % cellSize))
        if dy < cellSize / 2:
            ycoord.append(y - y % cellSize)
        else:
            ycoord.append(y + (cellSize - y % cellSize))

    releaseLine["xRaster"] = np.array(xcoord)
    releaseLine["yRaster"] = np.array(ycoord)

    return releaseLine


def computeSubArea(elevation, distance, surfElev, wetCellIdx, idx):
    """
    Computes flow subareas at the boundaries of a wetted cross section
    Handles the first (0) and last element (-1) of an index array

    Parameters
    -----------
    elevation: 1D-array
        the elevation of the cross-section cells
    distance: 1D-array
        the path along (distance) along the cross-section cells
    surfElev: float
        surface elevation of debris flow
    wetCellIdx: 1D-array
        indices of wetted cells
    idx: int
        0 or -1
        Starting or ending index

    Returns
    --------
    subarea: float
        flow subarea at the boundary of a wetted cross section
    dx: float
        horizontal distance that includes the flow subarea
    """

    if idx not in (0, -1):
        raise ValueError("idx must be 0 or -1")

    cellIdx = wetCellIdx[idx]

    if idx == 0:
        neighborIdx = cellIdx - 1
    elif idx == -1:
        neighborIdx = cellIdx + 1

    ds = abs(distance[neighborIdx] - distance[cellIdx])
    diffElev = elevation[neighborIdx] - elevation[cellIdx]
    slope = diffElev / ds
    th = surfElev - elevation[cellIdx]
    if slope == 0.0:
        dx = ds
    else:
        dx = th / slope

    subArea = 0.5 * th * dx

    return subArea, dx


def computeRatingCurve(crossSection, topoHydCfg):
    """
    compute relation between given discharge and flow thickness
    in a given topographic cross section

    Parameters
    -----------
    crossSection: dict
        dictionary containing x,y-coordinates of cross-section cells,
        the elevation of the cross-section cells,
        the path (distance) along the cross-section cells
    topoHydCfg: configparser object
        configuration settings for the in2TopoHyd-module

    Returns
    --------
    ratingCurve: dict
        dictionary containing
        thickness values/surface elevations and corresponding flow area
        minimum elevation of cross section (channel)
        min and max values of horizontal distance of flow area
    """
    # get the location of the lowest point of the cross section (channel)
    # channel is the area between the levee points
    idLevee = crossSection["idLevee"]
    elevLevee = crossSection["elevLevee"]
    elevation = crossSection["elevation"]
    minElev = np.min(elevation[min(idLevee) : max(idLevee) + 1])
    # horizontal distance between neighbouring cells
    distance = crossSection["s"]
    # get elevation steps
    dElev = topoHydCfg["GENERAL"].getfloat("dElev")

    # initialize lists
    thickness = []
    flowArea = []
    surfaceLevel = []
    xmin = []
    xmax = []

    # number of iteration steps
    numIt = (np.min(elevLevee) - minElev) / dElev
    numIt = math.floor(numIt)

    # routine loop: calculate flow area for given flow thickness
    for step in range(1, numIt + 1):
        # get surface level
        thick = step * dElev
        surfElev = minElev + thick
        # find indices of cells that are equal to or lie below surface level
        # search only in area between the two levee points
        idx = np.where(elevation[min(idLevee) : max(idLevee) + 1] <= surfElev)[0]
        idx = idx + min(idLevee)

        if len(idx) == 0:
            message = "Debris-flow surface level lies below the lowest channel elevation point!"
            log.error(message)
            raise ValueError(message)

        # np.trapz() only calculates the area between the vertices (cell centers)
        # if the thickness at the very left and the very right cell is still > 0,
        # there are remaining subareas on both sides that have to be considered
        areaLeft, dxLeft = computeSubArea(
            elevation=elevation, distance=distance, surfElev=surfElev, wetCellIdx=idx, idx=0
        )
        areaRight, dxRight = computeSubArea(
            elevation=elevation, distance=distance, surfElev=surfElev, wetCellIdx=idx, idx=-1
        )

        # get cell elevations and distances between cells
        elev = elevation[idx]
        dist = distance[idx]
        # compute flow area
        thickCells = surfElev - elev
        # TODO: function np.trapz was changed to np.trapezoid in later numpy versions
        flowArea.append(np.trapz(np.maximum(thickCells, 0), dist) + np.sum([areaLeft, areaRight]))

        # save results
        thickness.append(thick)
        surfaceLevel.append(surfElev)
        xmin.append(np.min(dist) - dxLeft)
        xmax.append(np.max(dist) + dxRight)

    ratingCurve = {
        "thickness": np.array(thickness),
        "flowArea": np.array(flowArea),
        "minElevation": minElev,
        "surfElev": np.array(surfaceLevel),
        "xmin": np.array(xmin),
        "xmax": np.array(xmax),
    }

    return ratingCurve


def computeSlope(dem, crossSection):
    """
    Computation of the slope of every DEM cell along the release line
    between levee points

    Parameters
    -----------
    dem: dict
        dictionary with dem header and rasterData (numpy nd array of z values)
    crossSection: dict
        dictionary containing
        x,y-coordinates of cross-section cells
        indices of cross-section cells along dem-raster

    Returns
    --------
    slope: float
        mean channel slope [m/m] between levee points
    """

    # the slope has to be in flow direction
    # get starting and ending points of cross section
    xcoordStart = crossSection["x"][0]
    ycoordStart = crossSection["y"][0]
    xcoordEnd = crossSection["x"][-1]
    ycoordEnd = crossSection["y"][-1]
    # get cell size of dem
    csz = dem["header"]["cellsize"]


    # get direction of cross section
    dx = xcoordEnd - xcoordStart
    dy = ycoordEnd - ycoordStart

    # calculate unit normal vectors on left- and right-handside
    # of direction vector
    nx1, ny1, _ = DFAtls.normalize(-dy, dx, 0)
    nx2, ny2, _ = DFAtls.normalize(dy, -dx, 0)

    # compute two additional cross sections on both handsides of the release line, respectively,
    # in distance d of original cross section
    d = 2 * np.sqrt(csz**2 + csz**2)
    # move starting and ending points of release line in direction of n1 and n2
    xcoordStart1 = xcoordStart + d * nx1
    ycoordStart1 = ycoordStart + d * ny1
    xcoordEnd1 = xcoordEnd + d * nx1
    ycoordEnd1 = ycoordEnd + d * ny1
    xcoordStart2 = xcoordStart + d * nx2
    ycoordStart2 = ycoordStart + d * ny2
    xcoordEnd2 = xcoordEnd + d * nx2
    ycoordEnd2 = ycoordEnd + d * ny2
    # save results in a dictionary
    coord1 = {"x": np.array([xcoordStart1, xcoordEnd1]), "y": np.array([ycoordStart1, ycoordEnd1])}
    coord2 = {"x": np.array([xcoordStart2, xcoordEnd2]), "y": np.array([ycoordStart2, ycoordEnd2])}
    # get elevation for new cross sections
    crossSect1 = getCrossSectionCells(dem, coord1)
    crossSect2 = getCrossSectionCells(dem, coord2)
    # between levee points
    start = min(crossSection["idLevee"])
    end = max(crossSection["idLevee"])
    # get mean elevation on each handside
    meanElev1 = np.mean(crossSect1["elevation"][start : end + 1])
    meanElev2 = np.mean(crossSect2["elevation"][start : end + 1])
    # get slope as central difference
    slope = abs((meanElev1 - meanElev2) / (2 * d))

    return slope


def computeRelFlowThVel(discharge, topoHydCfg, ratingCurve, dem, crossSection):
    """
    For a given discharge this function computes flow thickness (starting from the lowest point)
    and the mean velocity at a certain cross section.
    These flow thicknesses and velocities are used as starting condition.

    Parameters
    -----------
    discharge: 1D-array
        discharge value
    topoHydCfg: configparser object
        configuration settings for the in2TopoHyd-module
    ratingCurve: dict
        dictionary containing
        thickness values and corresponding flow area
    dem: dict
        dictionary with dem header and rasterData (numpy nd array of z values)
    crossSection: dict
        dictionary containing indices of cross-section cells along dem-raster

    Returns
    --------
    thickness: 1D-array
        flow thickness
    flowVel: 1D-array
        flow velocity
    """
    # TODO: same for other functions
    slope = topoHydCfg["GENERAL"].get("slope", fallback="")
    velType = topoHydCfg["GENERAL"].get("velType", fallback="rickenmann")

    # definition of the average slope of the cross section in flow direction
    if slope == "":
        slope = computeSlope(dem, crossSection)
    else:
        slope = float(slope)

    log.info(f"chosen slope: {slope:.2f}")

    flowVel = []
    # compute flow velocity
    if velType == "rickenmann":
        # flow velocity after Rickenmann (1999)
        for q in discharge:
            v = 2.1 * math.pow(q, 0.33) * math.pow(slope, 0.33)
            flowVel.append(v)

    # TODO: add additional methods for calculating the flow velocity

    else:
        message = "No velType defined!"
        log.error(message)
        raise ValueError(message)

    flowVel = np.round(np.array(flowVel), decimals=1)

    # calculate corresponding flow area
    flowArea = discharge / flowVel

    # fetch rating curve
    thicknessRC = ratingCurve["thickness"]
    flowAreaRC = ratingCurve["flowArea"]
    # check if the discharge is overtopping the channel
    idx = np.where(flowArea > max(flowAreaRC))[0]
    if len(idx) != 0:
        qOver = min(discharge[idx])
        message = "Discharge of at least %.02f is overtopping the debris-flow channel!" % qOver
        log.error(message)
        raise ValueError(message)
    # interpolate start flow thickness
    thickness = np.interp(flowArea, flowAreaRC, thicknessRC)
    thickness = np.round(thickness, decimals=2)

    return thickness, flowVel


def getCrossSectionCells(dem, releaseLine):
    """
    Get cells along the release line to generate a terrain cross section

    Parameters
    -----------
    dem: dict
        elevation raster data
    releaseLine: dict
        dictionary including starting and ending point of release line

    Returns
    --------
    crossSection: dict
        x,y-coordinates and elevation of cells along release line
        indices of cross-section cells along dem-raster
    """

    # get origin and cell size of DEM
    xllcenter = dem["header"]["xllcenter"]
    yllcenter = dem["header"]["yllcenter"]
    csz = dem["header"]["cellsize"]
    # get elevation data
    elevation = dem["rasterData"]

    # assign raster coords to starting and ending point of release line
    releaseLine = assignRasterCoords(csz, releaseLine)
    xcoordStart = releaseLine["xRaster"][0]
    ycoordStart = releaseLine["yRaster"][0]
    xcoordEnd = releaseLine["xRaster"][1]
    ycoordEnd = releaseLine["yRaster"][1]

    # get direction of release line
    dx = xcoordEnd - xcoordStart
    dy = ycoordEnd - ycoordStart

    # exception if the release line is a parallel to the
    # horizontal or the vertical of the DEM grid
    if dx == 0.0:
        num = abs(int(dy / csz)) + 1
        crossSectionY = np.linspace(ycoordStart, ycoordEnd, num)
        crossSectionX = np.array([xcoordStart] * len(crossSectionY))
    elif dy == 0.0:
        num = abs(int(dx / csz)) + 1
        crossSectionX = np.linspace(xcoordStart, xcoordEnd, num)
        crossSectionY = np.array([ycoordStart] * len(crossSectionX))
    else:
        # get x-coords of raster cells
        num = abs(int(dx / csz)) + 1
        crossSectionX = np.linspace(xcoordStart, xcoordEnd, num)
        # get distance along x-direction
        x = np.cumsum(np.diff(crossSectionX))
        x = np.insert(x, 0, 0)
        # get y-coords of raster cells
        crossSectionY = dy / dx * x + ycoordStart
        # get modulus of division by cell size
        modulus = crossSectionY % csz
        # round to values that are divisible by cell size
        crossSectionY = np.where(modulus < csz / 2, crossSectionY - modulus, crossSectionY + (csz - modulus))

    # get indices of cross-section cells
    col = np.int32(np.round((crossSectionX - xllcenter) / csz))
    row = np.int32(np.round((crossSectionY - yllcenter) / csz))
    # get elevation of cross-section cells
    elevCrossSection = elevation[row, col]

    crossSectIdx = np.array([row, col])

    crossSection = {
        "x": crossSectionX,
        "y": crossSectionY,
        "elevation": elevCrossSection,
        "crossSectIdx": crossSectIdx,
    }

    return crossSection


def getFlowDirection(crossSection, dem):
    """
    This function computes the flow direction.
    Normal to the cross section.

    Parameters
    -----------
    crossSection: dict
        dictionary containing x,y-coordinates of cross-section cells,
        the elevation of the cross-section cells,
        the path (distance) along the cross-section cells
    dem: dict
        elevation raster data


    Returns
    --------
    flwDir: 1D-array
        flow direction including x,y,z-components as unit normal vector of cross section

    """

    # get starting and ending points of cross section
    xcoordStart = crossSection["x"][0]
    ycoordStart = crossSection["y"][0]
    xcoordEnd = crossSection["x"][-1]
    ycoordEnd = crossSection["y"][-1]
    # get cell size of dem
    csz = dem["header"]["cellsize"]

    # get direction of cross section
    dx = xcoordEnd - xcoordStart
    dy = ycoordEnd - ycoordStart

    # calculate unit normal vectors on left- and right-handside
    # of direction vector; x-y-plane
    nx1, ny1, _ = DFAtls.normalize(-dy, dx, 0)
    nx2, ny2, _ = DFAtls.normalize(dy, -dx, 0)

    # compute two additional cross sections on both handsides of the release line, respectively,
    # in distance d of original cross section
    d = 2 * np.sqrt(csz**2 + csz**2)
    # move starting and ending points of release line in direction of n1 and n2
    xcoordStart1 = xcoordStart + d * nx1
    ycoordStart1 = ycoordStart + d * ny1
    xcoordEnd1 = xcoordEnd + d * nx1
    ycoordEnd1 = ycoordEnd + d * ny1
    xcoordStart2 = xcoordStart + d * nx2
    ycoordStart2 = ycoordStart + d * ny2
    xcoordEnd2 = xcoordEnd + d * nx2
    ycoordEnd2 = ycoordEnd + d * ny2
    # save results in a dictionary
    coord1 = {"x": np.array([xcoordStart1, xcoordEnd1]), "y": np.array([ycoordStart1, ycoordEnd1])}
    coord2 = {"x": np.array([xcoordStart2, xcoordEnd2]), "y": np.array([ycoordStart2, ycoordEnd2])}
    # get elevation for new cross sections
    crossSect1 = getCrossSectionCells(dem, coord1)
    crossSect2 = getCrossSectionCells(dem, coord2)
    # get mean elevation on each handside
    meanElev1 = np.mean(crossSect1["elevation"])
    meanElev2 = np.mean(crossSect2["elevation"])
    # get flow direction in x-y-plane
    if meanElev1 > meanElev2:
        flwDir = np.array([nx2, ny2])
    else:
        flwDir = np.array([nx1, ny1])

    # get z-component
    # get normal vector of the grid mesh
    demDict = {"header": dem["header"].copy(), "rasterData": dem["rasterData"]}
    demDict = geoTrans.getNormalMesh(demDict)
    NxNormed, NyNormed, NzNormed = DFAtls.normalize(demDict["Nx"], demDict["Ny"], demDict["Nz"])
    # compute z-component: 2D-vector must be rotated in 3D-space
    # normal vector of grid and normal vector of x-y-plane have to be perpendicular -> n * g = 0
    nz = -(flwDir[0] * NxNormed + flwDir[1] * NyNormed) / NzNormed

    # get normal vector along cross section
    row = crossSection["crossSectIdx"][0]
    col = crossSection["crossSectIdx"][1]
    nz = nz[row, col]
    # between levee points
    start = min(crossSection["idLevee"])
    end = max(crossSection["idLevee"])
    nz = nz[start : end + 1]
    nz = np.mean(nz)
    # combine to 3D-unit-normal vector
    flwDir = DFAtls.normalize(flwDir[0], flwDir[1], nz)
    flwDir = np.array(flwDir)

    return flwDir


def assignRelFlowTh(crossSection, ratingCurve, releaseThickness):
    """
    This function assigns a release flow thickness to any wet cell
    Starting from the lowest point of the channel (releaseThickness),
    the corresponding thicknesses are assigned to the other wet cells.

    Parameters
    -----------
    crossSection: dict
        dictionary containing x,y-coordinates of cross-section cells,
        the elevation of the cross-section cells,
        the path along (distance) along the cross-section cells
    ratingCurve: dict
        dictionary containing the minimum elevation of cross section (channel)
    releaseThickness: 1D-array
        array containing the release thickness values for each discharge value

    Returns
    --------
    wetCells: dict
        dictionary containing x,y-coordinates and thicknesses for any wet cell
    """

    xCoords = crossSection["x"]
    yCoords = crossSection["y"]
    elevation = crossSection["elevation"]
    idLevee = crossSection["idLevee"]
    minElev = ratingCurve["minElevation"]

    # only consider cross section between levee points
    elevation = elevation[min(idLevee) : max(idLevee) + 1]

    # identify wet cells
    # any cell that lies below debris-flow surface table is considered as wet
    thicknessCells = []
    wetXcoords = []
    wetYcoords = []

    for th in releaseThickness:
        # get surface level
        surfElev = minElev + th
        # find indices of cells that are equal to or lie below surface level
        idx = np.where(elevation <= surfElev)[0]
        # get cell flow thicknesses
        elev = elevation[idx]
        thickCells = np.round(surfElev - elev, decimals=2)
        thicknessCells.append(thickCells)
        # get x,y-coordinates of wet cells
        idx = min(idLevee) + idx
        wetXcoords.append(xCoords[idx])
        wetYcoords.append(yCoords[idx])

    wetCells = {"thicknessCells": thicknessCells, "wetXcoords": wetXcoords, "wetYcoords": wetYcoords}

    return wetCells


def plotCrossSection(crossSection, outputDir):
    """
    This function plots the terrain cross section

    Parameters
    -----------
    crossSection: dict
        dictionary containing
        the elevation of the cross-section cells and levee points,
        the path along (distance) along the cross-section cells
    outputDir: str or Path
        path to output directory of in2TopoHyd module

    Returns
    --------
    Plot: .png
        saves plot in debris-flow directory
    """

    # plot cross section
    fig, ax = plt.subplots(figsize=(10, 8))

    ax.plot(crossSection["s"], crossSection["elevation"])
    ax.scatter(crossSection["sLevee"], crossSection["elevLevee"], color="red", label="Levee points")
    ax.set_xlabel("distance [m]"), ax.set_ylabel("elevation [m]")
    ax.grid(color="gray", linestyle="--", linewidth=0.5, alpha=0.6)
    ax.set_title("Cross Section")

    plt.legend()
    plt.tight_layout()

    # check if directory already exists
    path = outputDir / "Plots"
    fU.makeADir(path)

    fig.savefig(path / "crossSection.png")


def plotRatingCurve(ratingCurve, crossSection, outputDir):
    """
    This function plots the terrain cross section
    and the corresponding rating curve

    Parameters
    -----------
    ratingCurve: dict
        dictionary containing
        thickness values/surface elevations and corresponding flow area
        min and max values of horizontal distance of flow area
    crossSection: dict
            dictionary containing
            the elevation of the cross-section cells,
            the path along (distance) along the cross-section cells
    outDir: str or Path
            path to output directory of in2TopoHyd module

    Returns
    --------
    Plot: .png
        saves plot in debris-flow directory
    """

    thickness = ratingCurve["thickness"]
    flowArea = ratingCurve["flowArea"]
    surfElev = ratingCurve["surfElev"]
    xmin = ratingCurve["xmin"]
    xmax = ratingCurve["xmax"]

    # plot cross section
    fig, ax = plt.subplots(ncols=1, nrows=2, figsize=(10, 8))

    ax[0].plot(crossSection["s"], crossSection["elevation"])
    ax[0].scatter(crossSection["sLevee"], crossSection["elevLevee"], color="red", label="Levee points")
    ax[0].hlines(
        surfElev, xmin=xmin, xmax=xmax, linestyles="--", colors="grey", lw=0.5, label="elevation increments"
    )
    ax[0].set_xlabel("distance [m]"), ax[0].set_ylabel("elevation [m]")
    ax[0].grid(color="gray", linestyle="--", linewidth=0.5, alpha=0.6)
    ax[0].set_title("Cross Section")
    ax[0].legend()

    ax[1].plot(thickness, flowArea)
    ax[1].set_xlabel("flow thickness [m]"), ax[1].set_ylabel("flow area [m²]")
    ax[1].grid(color="gray", linestyle="--", linewidth=0.5, alpha=0.6)
    ax[1].set_title("Rating Curve")

    plt.tight_layout()

    path = outputDir / "Plots" / "ratingCurve.png"
    fig.savefig(path)


def in2TopoHydMain(debrisDir, topoHydCfg, debrisCfg):
    """
    Main script to get the initial conditions for a release line as a csv-file

    Parameters
    -----------
    debrisDir: str or pathlib path
        path to debris-flow directory
    topoHydCfg: configparser.ConfigParser
        configuration file for the in2TopoHyd-module
    debrisCfg: configparser.ConfigParser
            configuration file for the c1TIF-module

    Returns
    --------
    csv-file with initial conditions at the release line
    Plots of cross section and rating curve
    cross-section cell centers as csv-file - optional

    """

    # create output directory
    outputDir = pathlib.Path(debrisDir, "Outputs", "in2TopoHyd")
    fU.makeADir(outputDir)

    # +++ 1. read input data
    log.info("Read input data")

    # get dem
    dem = gI.initializeDEM(debrisDir)

    # get file name of release line
    # first, check if name is provided in the c1TIF-config file
    inputDir = pathlib.Path(debrisDir, "Inputs")
    fname, *_ = gI.getAndCheckInputFiles(inputDir=inputDir, inputType="cross section", folder="XSECT")

    # get release line
    releaseLine = shpConv.readLine(fname, "release1", dem)

    log.info(f"release line used: {fname}")

    # fetch number of points
    nPoints = len(releaseLine["x"])
    # check if line includes only two points: starting and ending point
    if nPoints != 2:
        message = "Release line consists of more/less than 2 points! Only starting and ending point allowed!"
        log.error(message)
        raise ValueError(message)

    # get file name of levee points
    inputDir = pathlib.Path(debrisDir, "Inputs")
    fname, *_ = gI.getAndCheckInputFiles(inputDir=inputDir, inputType="Levee", folder="LEVEE")

    # get levee points
    leveePoints = shpConv.readLine(fname, "release1", dem)

    log.info(f"levee points used: {fname}")

    # +++ 2. get all cells along the release line
    log.info("Get all cells along the release line")

    # get cross section cells
    crossSection = getCrossSectionCells(dem, releaseLine)
    # get distance between cells
    crossSection = geoTrans.computeS(crossSection)

    # assign levee points to neares cross-section coordinates
    crossSection = assignCrossSectionCoords(leveePoints, crossSection)

    # export cross section cell centers as points for plausibility check
    if topoHydCfg["EXPORTS"].getboolean("exportCrossSectionCells"):
        file = pd.DataFrame(
            {"x": crossSection["x"], "y": crossSection["y"], "elev": crossSection["elevation"]}
        )
        path = outputDir / "crossSectionCells.csv"
        file.to_csv(path, sep=",", decimal=".", header=True, index=False)

    plotCrossSection(crossSection=crossSection, outputDir=outputDir)

    # +++ 4. calculate hydraulic boundary conditions
    log.info("Calculate hydraulic boundary conditions")

    # compute rating curve
    ratingCurve = computeRatingCurve(crossSection, topoHydCfg)

    # plot cross section and rating curve for plausibility check
    plotRatingCurve(ratingCurve=ratingCurve, crossSection=crossSection, outputDir=outputDir)

    # compute release flow thicknesses and velocities
    # get file name of hydrograph
    fname, *_ = gI.getAndCheckInputFiles(
        inputDir=inputDir, folder="HYDR", inputType="Hydrograph", fileExt="csv"
    )
    # read hydrograph
    hydrograph = pd.read_csv(fname, sep=",", decimal=".", header=0)
    discharge = np.array(hydrograph["discharge"])
    timestep = np.array(hydrograph["timestep"])

    log.info(f"hydrograph used: {fname}")

    # get release flow thicknesses and velocities
    relTh, vel = computeRelFlowThVel(
        discharge, topoHydCfg, ratingCurve=ratingCurve, dem=dem, crossSection=crossSection
    )

    # distribute mean flow thickness over wetted cells
    wetCells = assignRelFlowTh(crossSection, ratingCurve, relTh)

    # +++ 5. get flow direction
    log.info("Get flow direction")

    # normal to release line
    # Vx, Vy, Vz -> vel magnitude multiplied by unit vector of direction
    flwDirection = getFlowDirection(crossSection=crossSection, dem=dem)
    vx = np.round(vel * flwDirection[0], decimals=2)
    vy = np.round(vel * flwDirection[1], decimals=2)
    vz = np.round(vel * flwDirection[2], decimals=2)

    # +++ 6. export x,y-coords, timesteps, thickness and x,y,z(?)-velocities to csv-file
    log.info("Export csv-file")

    time = []
    th = []
    velx = []
    vely = []
    velz = []
    x = []
    y = []
    for t, i in enumerate(timestep):
        for j in range(len(wetCells["wetXcoords"][t])):
            time.append(i)
            th.append(wetCells["thicknessCells"][t][j])
            velx.append(vx[t])
            vely.append(vy[t])
            velz.append(vz[t])
            x.append(wetCells["wetXcoords"][t][j])
            y.append(wetCells["wetYcoords"][t][j])

    output = pd.DataFrame(
        {
            "timestep": time,
            "thickness": th,
            "velocityX": velx,
            "velocityY": vely,
            "velocityZ": velz,
            "x": x,
            "y": y,
        }
    )

    output.to_csv(outputDir / "initCondHyd.csv", sep=",", decimal=".", header=True, index=False)
