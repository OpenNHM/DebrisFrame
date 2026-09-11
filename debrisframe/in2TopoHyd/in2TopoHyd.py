"""
Get initial conditions for hydrograph
"""

# Load modules
import pathlib
import math
import logging
import configparser
import numpy as np
import pandas as pd

# local imports
from avaframe.in1Data import getInput as gI
from avaframe.in3Utils import geoTrans
import avaframe.in2Trans.shpConversion as shpConv
import avaframe.com1DFA.DFAtools as DFAtls
import avaframe.in3Utils.fileHandlerUtils as fU

import debrisframe.in1Utils.plotUtils as pltUtls

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
        idPoint.append(np.argmin(dist))

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


def assignRasterCoords(cellSize, xllcenter, yllcenter, releaseLine):
    """
    Assign nearest raster coordinates to the release line

    Parameters
    -----------
    cellSize: int
        dem cell size
    xllcenter: float
        x-coordinate of the dem origin (cell center)
    yllcenter: float
        y-coordinate of the dem origin (cell center)
    releaseLine: dict
        dictionary including starting and ending point of release line

    Returns
    --------
    releaseLine: dict
        dictionary including new coordinates for start and ending point
    """

    # assign raster cell coord to starting and ending point of release line
    # snap relative to cell centers, not to global multiples of the cell size
    xcoord = []
    ycoord = []
    for x, y in zip(releaseLine["x"], releaseLine["y"]):
        xcoord.append(xllcenter + np.round((x - xllcenter) / cellSize) * cellSize)
        ycoord.append(yllcenter + np.round((y - yllcenter) / cellSize) * cellSize)

    releaseLine["xRaster"] = np.array(xcoord)
    releaseLine["yRaster"] = np.array(ycoord)

    return releaseLine


def computeSubArea(elevation, distance, surfElev, idLevee, wetCellIdx, idx):
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
    idLevee: 1D-array
        indices of levee points
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

    if cellIdx in idLevee:
        dx = 0.0

    subArea = 0.5 * th * dx

    return subArea, dx


def computeRatingCurve(crossSection, topoHydCfg):
    """
    compute relation between flow area and flow thickness
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
    if numIt <= 0:
        message = (
            "Channel is flat between the levee points or the levee points do not lie above the "
            "channel bottom! Cannot compute a rating curve."
        )
        log.error(message)
        raise ValueError(message)

    # routine loop: calculate flow area for given flow thickness
    for step in range(1, numIt + 1):
        # get surface level
        thick = step * dElev
        surfElev = minElev + thick
        # find indices of cells that are equal to or lie below surface level
        # search only in area between the two levee points
        idx = np.where(elevation[min(idLevee) : max(idLevee) + 1] <= surfElev)[0]
        idx = idx + min(idLevee)
        # find breaking points in elevation array which lie over surfElev due to unevenness of ground
        idxOver = np.where(np.diff(idx) != 1)[0]
        # get subarrays between breaking points
        idxSub = np.split(idx, idxOver + 1)

        if len(idx) == 0:
            message = "Debris-flow surface level lies below the lowest channel elevation point!"
            log.error(message)
            raise ValueError(message)

        subFlwArea = []
        subXmin = []
        subXmax = []
        # iteration loop over subarrays
        for sub in idxSub:

            # np.trapz() only calculates the area between the vertices (cell centers)
            # if the thickness at the very left and the very right cell is still > 0,
            # there are remaining subareas on both sides that have to be considered
            areaLeft, dxLeft = computeSubArea(
                elevation=elevation,
                distance=distance,
                surfElev=surfElev,
                idLevee=idLevee,
                wetCellIdx=sub,
                idx=0,
            )
            areaRight, dxRight = computeSubArea(
                elevation=elevation,
                distance=distance,
                surfElev=surfElev,
                idLevee=idLevee,
                wetCellIdx=sub,
                idx=-1,
            )

            # get cell elevations and distances between cells
            elev = elevation[sub]
            dist = distance[sub]
            # compute flow area
            thickCells = surfElev - elev
            # TODO: function np.trapz was changed to np.trapezoid in later numpy versions
            subFlwArea.append(np.trapz(np.maximum(thickCells, 0), dist) + np.sum([areaLeft, areaRight]))
            # get xmin and xmax for subarrays; for plotting the elevation increments
            subXmin.append(np.min(dist) - dxLeft)
            subXmax.append(np.max(dist) + dxRight)

        # save results
        flowArea.append(np.sum(subFlwArea))
        thickness.append(thick)
        surfaceLevel.append(surfElev)
        xmin.append(subXmin)
        xmax.append(subXmax)

    ratingCurve = {
        "thickness": np.array(thickness),
        "flowArea": np.array(flowArea),
        "minElevation": minElev,
        "surfElev": np.array(surfaceLevel),
        "xmin": xmin,
        "xmax": xmax,
    }

    return ratingCurve


def computeParallelCrossSection(dem, crossSection, topoHydCfg):
    """
    Generates two parallel cross sections in a predefined normal distance
    on each side of the original release line and computes the mean
    elevation along these cross sections between the levee points.

    Parameters
    -----------
    dem: dict
        dictionary with dem header and rasterData (numpy nd array of z values)
    crossSection: dict
        dictionary containing
        x,y-coordinates of cross-section cells
        indices of cross-section cells along dem-raster
    topoHydCfg: configparser object
        configuration settings for the in2TopoHyd-module

    Returns
    --------
    meanElev1, meanElev2: float
        mean elevations of the newly generated cross sections
    normalDist: float
        normal distance to release line
    unitNormVec1, unitNormVec2: 1D-array
        unit normal vectors pointing away from release line

    """

    # get starting and ending points of cross section
    xcoordStart = crossSection["x"][0]
    ycoordStart = crossSection["y"][0]
    xcoordEnd = crossSection["x"][-1]
    ycoordEnd = crossSection["y"][-1]
    # get cell size of dem
    csz = dem["header"]["cellsize"]
    # get normal distance to release line
    normalDist = topoHydCfg["GENERAL"].get("normalDist", fallback="")

    # get direction of cross section
    dx = xcoordEnd - xcoordStart
    dy = ycoordEnd - ycoordStart

    # calculate unit normal vectors on left- and right side
    # of direction vector
    nx1, ny1, _ = DFAtls.normalize(-dy, dx, 0)
    nx2, ny2, _ = DFAtls.normalize(dy, -dx, 0)

    # compute two additional cross sections on both handsides of the release line, respectively,
    # in distance d of original cross section
    if normalDist == "":
        normalDist = 2 * np.sqrt(csz**2 + csz**2)
    else:
        normalDist = float(normalDist)
    # move starting and ending points of release line in direction of n1 and n2
    xcoordStart1 = xcoordStart + normalDist * nx1
    ycoordStart1 = ycoordStart + normalDist * ny1
    xcoordEnd1 = xcoordEnd + normalDist * nx1
    ycoordEnd1 = ycoordEnd + normalDist * ny1
    xcoordStart2 = xcoordStart + normalDist * nx2
    ycoordStart2 = ycoordStart + normalDist * ny2
    xcoordEnd2 = xcoordEnd + normalDist * nx2
    ycoordEnd2 = ycoordEnd + normalDist * ny2
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

    unitNormVec1 = np.array([nx1, ny1])
    unitNormVec2 = np.array([nx2, ny2])

    return meanElev1, meanElev2, normalDist, unitNormVec1, unitNormVec2


def computeSlopeAlongChannel(dem, crossSection, topoHydCfg):
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
    topoHydCfg: configparser object
        configuration settings for the in2TopoHyd-module

    Returns
    --------
    slope: float
        mean channel slope [m/m] between levee points
    """

    # get up-/downstream elevations and distance between auxiliary cross sections
    meanElev1, meanElev2, normalDist, *_ = computeParallelCrossSection(dem, crossSection, topoHydCfg)
    # get slope as central difference
    slope = abs((meanElev1 - meanElev2) / (2 * normalDist))

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
    meanFlowVel: 1D-array
        flow velocity
    """

    slope = topoHydCfg["GENERAL"].get("slope", fallback="")
    velType = topoHydCfg["GENERAL"].get("velType", fallback="rickenmann")

    if velType == "":
        message = "velType not defined!"
        log.error(message)
        raise ValueError(message)
    supportedVelTypes = ("rickenmann",)
    if velType not in supportedVelTypes:
        message = f"velType '{velType}' not supported! Supported values: {', '.join(supportedVelTypes)}"
        log.error(message)
        raise ValueError(message)
    # TODO: necessary when fallback is active?

    # definition of the average slope of the cross section in flow direction
    if slope == "":
        slope = computeSlopeAlongChannel(dem, crossSection, topoHydCfg)
    else:
        slope = float(slope)

    log.info(f"chosen slope: {slope:.2f}")

    # compute mean flow velocity for every time interval
    if velType == "rickenmann":
        # flow velocity after Rickenmann (1999)
        meanFlowVel = [
            2.1
            * math.pow(slope, 0.33)
            * 0.5
            * (math.pow(discharge[q], 0.33) + math.pow(discharge[q + 1], 0.33))
            for q in range(len(discharge) - 1)
        ]
    # TODO: add additional methods for calculating the flow velocity

    meanFlowVel = np.array(meanFlowVel)

    # get mean discharge for every time interval
    meanDischarge = [(discharge[q] + discharge[q + 1]) * 0.5 for q in range(len(discharge) - 1)]
    # calculate corresponding flow area
    flowArea = meanDischarge / meanFlowVel

    # fetch rating curve
    thicknessRC = ratingCurve["thickness"]
    flowAreaRC = ratingCurve["flowArea"]
    # check if the discharge is overtopping the channel
    # TODO: allow overtopping
    idx = np.where(flowArea > max(flowAreaRC))[0]
    if len(idx) != 0:
        qOver = min(discharge[idx])
        message = "Discharge of at least %.02f m³/s is overtopping the debris-flow channel!" % qOver
        log.error(message)
        raise ValueError(message)
    # interpolate start flow thickness
    thickness = np.interp(flowArea, flowAreaRC, thicknessRC)

    meanFlowVel = np.round(meanFlowVel, decimals=1)

    return thickness, meanFlowVel


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
        x,y-coordinates, elevation and actual area of cells along release line
        indices of cross-section cells along dem-raster
    """

    # get origin and cell size of DEM
    xllcenter = dem["header"]["xllcenter"]
    yllcenter = dem["header"]["yllcenter"]
    csz = dem["header"]["cellsize"]
    # get elevation data
    elevation = dem["rasterData"]
    # get actual cell area
    actualArea = dem["areaRaster"]

    # assign raster coords to starting and ending point of release line
    releaseLine = assignRasterCoords(csz, xllcenter, yllcenter, releaseLine)
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
        # snap to nearest cell center, not to global multiples of the cell size
        crossSectionY = yllcenter + np.round((crossSectionY - yllcenter) / csz) * csz

    # get indices of cross-section cells
    col = np.int32(np.round((crossSectionX - xllcenter) / csz))
    row = np.int32(np.round((crossSectionY - yllcenter) / csz))
    # get elevation of cross-section cells
    elevCrossSection = elevation[row, col]

    # get actual area of cross-section cells
    cellAreaCrossSection = actualArea[row, col]

    crossSectIdx = np.array([row, col])

    crossSection = {
        "x": crossSectionX,
        "y": crossSectionY,
        "elevation": elevCrossSection,
        "actualCellArea": cellAreaCrossSection,
        "crossSectIdx": crossSectIdx,
    }

    return crossSection


def getDEMRaster(debrisDir, debrisCfg):
    """
    Reads DEM data (ascii or tif) from a provided debris-flow directory.

    Parameters
    -----------
    debrisDir: str or pathlib path
        path to debris-flow directory
    debrisCfg: configparser.ConfigParser
        configuration file for the c1TIF-module

    Returns
    --------
    dem: dict
        dict with header, raster data and cell areas

    """

    # read DEM from debris-flow directory path
    dem = gI.readDEM(debrisDir)
    cellsize = dem["header"]["cellsize"]
    meshCellSize = debrisCfg.getfloat("com1DFA_com1DFA_override", "meshCellSize")
    # check if desired mesh cell sizes matches the cell size of the actual DEM
    if cellsize != meshCellSize:
        # TODO: get fallback values from default config file?
        # get parameters
        meshCellSizeThreshold = debrisCfg["com1DFA_com1DFA_override"].get(
            "meshCellSizeThreshold", fallback="0.001"
        )
        remeshInterpMethod = debrisCfg["com1DFA_com1DFA_override"].get(
            "remeshInterpMethod", fallback="default"
        )
        cfgRaster = configparser.ConfigParser()
        cfgRaster["GENERAL"] = {
            "meshCellSize": meshCellSize,
            "meshCellSizeThreshold": meshCellSizeThreshold,
            "remeshInterpMethod": remeshInterpMethod,
            "avalancheDir": debrisDir,
        }
        # remesh DEM
        rasterPath = gI.getDEMPath(debrisDir)
        rasterPath = geoTrans.remeshRaster(rasterPath, cfgRaster)
        dem = gI.initializeDEM(debrisDir, rasterPath)

        log.info(f"DEM used: {rasterPath}")
    else:
        log.info(f"DEM used: {gI.getDEMPath(debrisDir)}")
    # get actual cell area
    dem = geoTrans.getNormalMesh(dem, 4)
    dem = DFAtls.getAreaMesh(dem, 4)

    return dem


def getFlowDirection(crossSection, dem, topoHydCfg):
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
    topoHydCfg: configparser object
        configuration settings for the in2TopoHyd-module

    Returns
    --------
    flwDir: 1D-array
        flow direction including x,y,z-components as unit normal vector of cross section

    """

    # get up-/downstream elevations and distance between auxiliary cross sections
    meanElev1, meanElev2, _, unitNormVec1, unitNormVec2 = computeParallelCrossSection(
        dem, crossSection, topoHydCfg
    )
    # get flow direction in x-y-plane
    if meanElev1 > meanElev2:
        flwDir = unitNormVec2
    else:
        flwDir = unitNormVec1

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


def getHydrograph(inputDir):
    """
    Reads data from input hydrograph csv-file.

    Parameters
    -----------
    inputDir: pathlib path
        path to debrisDir/Inputs

    Returns
    --------
    hydrograph: dict
        dict with timestep, discharge and release volume
    """

    # get file name of hydrograph
    fname, *_ = gI.getAndCheckInputFiles(
        inputDir=inputDir, folder="HYDR", inputType="Hydrograph", fileExt="csv"
    )
    if fname is None:
        message = "No hydrograph csv-file in Inputs/HYDR!"
        log.error(message)
        raise FileNotFoundError(message)

    # read hydrograph from csv
    hydrograph = pd.read_csv(fname, sep=",", decimal=".", header=0)
    discharge = np.array(hydrograph["discharge"])
    timestep = np.array(hydrograph["timestep"])
    # check if time steps are equidistant
    dt = np.unique(np.diff(timestep))
    if len(dt) != 1:
        message = "time interval of hydrograph is not uniform!"
        log.error(message)
        raise ValueError(message)
    # get release volume for every time step
    relVol = [float((discharge[t + 1] + discharge[t]) * 0.5 * dt[0]) for t in range(len(timestep) - 1)]
    relVol = np.array(relVol)

    # create dictionary
    hydrograph = {}
    hydrograph["timestep"] = timestep
    hydrograph["discharge"] = discharge
    hydrograph["relVol"] = relVol

    log.info(f"hydrograph used: {fname}")

    return hydrograph


def getInputShapeFiles(inputDir, folder, fileType, dem):
    """
    Reads release line and levee point data from input shapefiles

    Parameters
    -----------
    inputDir: pathlib path
        path to debrisDir/Inputs
    folder: str
        name of folder where the shapefile is located
    fileType: str
        "Release line" or "Levee points"
    dem: dict
        dem dictionary

    Returns
    --------
    Line : dict
        Line['Name'] : list of lines names
        Line['Coord'] : np array of the coords of points in lines
        Line['Start'] : list of starting index of each line in Coord
        Line['Length'] : list of length of each line in Coord
    """

    # get file name
    fname, *_ = gI.getAndCheckInputFiles(inputDir=inputDir, inputType=fileType, folder=folder)
    if fname is None:
        message = f"No {fileType} shp-file in Inputs/{folder}!"
        log.error(message)
        raise FileNotFoundError(message)

    # get release line
    shapeFile = shpConv.readLine(fname, "release1", dem)

    # fetch number of points
    nPoints = len(shapeFile["x"])
    # check if shapefile includes only two points: starting and ending point
    if nPoints != 2:
        message = f"{fileType} consists of more/less than 2 points! Only starting and ending point allowed!"
        log.error(message)
        raise ValueError(message)

    log.info(f"{fileType} used: {fname}")

    return shapeFile


def assignToWetCell(crossSection, dem, ratingCurve, releaseThickness, releaseVolume):
    """
    This function assigns release flow thickness and release volumina to any wet cell

    Parameters
    -----------
    crossSection: dict
        dictionary containing x,y-coordinates of cross-section cells,
        the elevation of the cross-section cells,
        the path along (distance) along the cross-section cells
    dem: dict
        elevation raster data
    ratingCurve: dict
        dictionary containing the minimum elevation of cross section (channel)
    releaseThickness: 1D-array
        array containing the release thickness values for each discharge value
    releaseVolume: 1D-array
        array containing the release volume values for each discharge value

    Returns
    --------
    wetCells: dict
        dictionary containing x,y-coordinates, thicknesses and release volumina for any wet cell
    """

    xCoords = crossSection["x"]
    yCoords = crossSection["y"]
    elevation = crossSection["elevation"]
    idLevee = crossSection["idLevee"]
    actCellArea = crossSection["actualCellArea"]
    minElev = ratingCurve["minElevation"]
    csz = dem["header"]["cellsize"]

    # only consider cross section between levee points
    elevation = elevation[min(idLevee) : max(idLevee) + 1]

    # identify wet cells
    # any cell that lies below debris-flow surface table is considered as wet
    thicknessCells = []
    relVol = []
    wetXcoords = []
    wetYcoords = []
    thicknessCellsVol = []

    for i, th in enumerate(releaseThickness):
        # get surface level
        surfElev = minElev + th
        # find indices of cells that are equal to or lie below surface level
        idx = np.where(elevation < surfElev)[0]
        # get cell flow thicknesses
        elev = elevation[idx]
        # thickCells = np.round(surfElev - elev, decimals=2)
        thickCells = surfElev - elev
        thicknessCells.append(thickCells)
        # distribute release volumina due to the cells area proportions
        # get sub-flow areas
        idx = min(idLevee) + idx
        subAreas = thickCells * csz
        # compute area proportions
        coeff = subAreas / np.sum(subAreas)
        # distribute release volumina
        # volume = np.round(releaseVolume[i] * coeff, decimals=2)
        volume = releaseVolume[i] * coeff
        relVol.append(volume)
        # distribute thickness calculated from cell area and cell volume
        thickCellsVol = volume / (actCellArea[idx])
        thicknessCellsVol.append(thickCellsVol)
        # get x,y-coordinates of wet cells
        wetXcoords.append(xCoords[idx])
        wetYcoords.append(yCoords[idx])

    wetCells = {
        "thicknessCells": thicknessCells,
        "releaseVolume": relVol,
        "wetXcoords": wetXcoords,
        "wetYcoords": wetYcoords,
        "thicknessCellsVol": thicknessCellsVol,
    }

    return wetCells


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

    # TODO: # Clean input directory(ies) of old work files?
    # initProj.cleanSingleAvaDir(debrisDir, deleteOutput=False)

    # create output directory
    outputDir = pathlib.Path(debrisDir, "Outputs", "in2TopoHyd")
    fU.makeADir(outputDir)

    # +++ 1. read input data
    log.info("Read input data")

    # get dem
    dem = getDEMRaster(debrisDir, debrisCfg)

    # get release line and levee points
    inputDir = pathlib.Path(debrisDir, "Inputs")
    releaseLine = getInputShapeFiles(inputDir=inputDir, folder="XSECT", fileType="Release line", dem=dem)
    leveePoints = getInputShapeFiles(inputDir=inputDir, folder="LEVEE", fileType="Levee points", dem=dem)

    # +++ 2. get all cells along the release line
    log.info("Get all cells along the release line")

    # get cross section cells
    crossSection = getCrossSectionCells(dem, releaseLine)
    # get distance between cells
    crossSection = geoTrans.computeS(crossSection)

    # assign levee points to nearest cross-section coordinates
    crossSection = assignCrossSectionCoords(leveePoints, crossSection)

    # export cross section cell centers as points for plausibility check
    if topoHydCfg["EXPORTS"].getboolean("exportCrossSectionCells"):
        file = pd.DataFrame(
            {"x": crossSection["x"], "y": crossSection["y"], "elev": crossSection["elevation"]}
        )
        path = outputDir / "crossSectionCells.csv"
        file.to_csv(path, sep=",", decimal=".", header=True, index=False)

    pltUtls.plotCrossSection(crossSection=crossSection, outputDir=outputDir)

    # +++ 4. calculate hydraulic boundary conditions
    log.info("Calculate hydraulic boundary conditions")

    # compute rating curve
    ratingCurve = computeRatingCurve(crossSection, topoHydCfg)

    # plot cross section and rating curve for plausibility check
    pltUtls.plotRatingCurve(ratingCurve=ratingCurve, crossSection=crossSection, outputDir=outputDir)

    # get hydrograph data
    hydrograph = getHydrograph(inputDir)

    # get release flow thicknesses and velocities
    relTh, vel = computeRelFlowThVel(
        hydrograph["discharge"], topoHydCfg, ratingCurve=ratingCurve, dem=dem, crossSection=crossSection
    )

    # distribute flow thickness and release volume over wetted cells
    wetCells = assignToWetCell(crossSection, dem, ratingCurve, relTh, hydrograph["relVol"])

    # +++ 5. get flow direction
    log.info("Get flow direction")

    # normal to release line
    # Vx, Vy, Vz -> vel magnitude multiplied by unit vector of direction
    flwDirection = getFlowDirection(crossSection=crossSection, dem=dem, topoHydCfg=topoHydCfg)
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
    for t, i in enumerate(hydrograph["timestep"][:-1]):
        for j in range(len(wetCells["wetXcoords"][t])):
            time.append(i)
            th.append(wetCells["thicknessCellsVol"][t][j])
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
