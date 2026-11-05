"""
Main module for c2TopRunDF: semi-empirical debris flow deposition simulation based on pyTopRunDF

@author: Christian Scheidl

(modified by Paula Spannring)
"""

# Load modules
import logging
import mmap
import pathlib

import geopandas as gpd
import matplotlib as mpl
import numpy as np
import rasterio
from scipy.ndimage import convolve

# AvaFrame imports
import avaframe.in1Data.getInput as gI
import avaframe.in2Trans.rasterUtils as rasterUtils
import avaframe.in3Utils.initialiseDirs as iD
import avaframe.in3Utils.initializeProject as initProj

import debrisframe.c2TopRunDF.pyTopRunDFRepo.RandomSingleFlow as randomsfp
from debrisframe.c2TopRunDF.pyTopRunDFRepo.PlotResult import HillshadePlotter

# To get a reproducible result, set the seed:
# np.random.seed(42)

# create local logger under avaframe namespace to use its logging configuration
log = logging.getLogger("avaframe.debrisframe.c2TopRunDF")

# Set global font size for plots
mpl.rcParams["font.size"] = 8
mpl.rcParams["axes.titlesize"] = 12
mpl.rcParams["axes.labelsize"] = 8
mpl.rcParams["xtick.labelsize"] = 8
mpl.rcParams["ytick.labelsize"] = 8


def c2TopRunDFMain(cfgMain, cfgDebris):
    """Run the c2TopRunDF simulation for one scenario
    and writes the deposition raster (depo.asc) to Outputs/c2TopRunDF and plots the result

    Parameters
    ------------
    cfgMain : configparser object
        main configuration (avalancheDir in section MAIN)
    cfgDebris : configparser object
        c2TopRunDF configuration (section GENERAL)
    """

    # TODO: allow computing several scenarios in one run (only for one DEM -> difference to original!!!)

    cfgGen = cfgDebris["GENERAL"]
    avaDir = cfgMain["MAIN"]["avalancheDir"]
    initProj.cleanSingleAvaDir(avaDir, deleteOutput=False)
    outputDir, demFile = initializeSimulation(avaDir)

    # get input data
    eventName = cfgGen["name"]
    volume = cfgGen.getfloat("volume")
    coefficient = cfgGen.getfloat("coefficient")
    cfgGen, xCoord, yCoord = getReleaseCoordinates(cfgGen, avaDir)

    energyHeight = cfgGen["energyHeight"]
    if energyHeight != "elevation":
        energyHeight = parseDecimal(str(energyHeight))

    # Preprocess the DEM file if necessary (comma as decimal separator) and open it
    processedDemFile = preprocessRaster(demFile)
    demData = rasterUtils.readRaster(processedDemFile, noDataToNan=False)
    # TODO: only work with the open rasterio file or also read in raster data and header?
    demDataset = rasterio.open(processedDemFile)

    # Initialize variables
    cellSize = demData["header"]["cellsize"]
    simArea = volume ** (2 / 3) * coefficient
    perimeter = simArea / cellSize ** 2
    startRow, startCol = demDataset.index(xCoord, yCoord)

    # Flow path simulation
    hitCount = simulateFlowPaths(
        demDataset, demData, startRow, startCol, perimeter, energyHeight, outputDir, cfgGen
    )

    # Distribute the volume on the deposition area
    depoHeight = computeDepositionHeight(hitCount, volume, perimeter, cellSize, cfgGen)

    # Save the output raster
    outMeta = demDataset.meta.copy()
    demDataset.close()
    outMeta.update({"driver": "AAIGrid", "dtype": "float32"})
    outputRasterPath = outputDir / "depo.asc"
    with rasterio.open(outputRasterPath, "w", **outMeta) as dest:
        dest.write(depoHeight, 1)

    # Clean up the temporary file if preprocessing was done
    if processedDemFile != demFile:
        processedDemFile.unlink()

    log.info("Simulation finished")

    # Generate the plot
    plotter = HillshadePlotter()
    plotter.plot(outputRasterPath, demFile, eventName, outputDir)


def initializeSimulation(avaDir):
    """Fetch the DEM path and initialise the output directory

    Parameters
    ------------
    avaDir : str or pathlib Path
        path to debris flow directory

    Returns
    ------------
    outputDir : pathlib Path
        path to the output directory (avaDir/Outputs/c2TopRunDF)
    demFile : pathlib Path
        path to the DEM file
    """

    demFile = gI.getDEMPath(avaDir)
    _, outputDir = iD.initialiseRunDirs(avaDir, modName="c2TopRunDF", cleanRemeshedRasters=False)
    return outputDir, demFile


def getReleaseCoordinates(cfgGen, avaDir):
    """Get the release point coordinates from the configuration or the release point shp file

    If xKoord or yKoord are empty in the configuration, the release point is read from
    the shp file in avaDir/Inputs/REL

    Parameters
    ------------
    cfgGen : configparser section
        GENERAL section of the c2TopRunDF configuration
    avaDir : str or pathlib Path
        path to debris flow directory

    Returns
    ------------
    cfgGen: configparser section
        GENERAL section of the c2TopRunDF configuration with updated "relPointFromShp"
    xCoord : float
        x coordinate of release point
    yCoord : float
        y coordinate of release point
    """

    if cfgGen.get("xKoord") == "" or cfgGen.get("yKoord") == "":
        cfgGen["relPointFromShp"] = "True"
    else:
        cfgGen["relPointFromShp"] = "False"
        xCoord = cfgGen.getfloat("xKoord")
        yCoord = cfgGen.getfloat("yKoord")

    # coordinates given in the configuration have priority over the release point shp file
    if cfgGen.getboolean("relPointFromShp"):
        inputDir = pathlib.Path(avaDir, "Inputs")
        xCoord, yCoord = getCoordinatesFromPoint(inputDir)
    else:
        log.info("release point coordinates are read from the configuration")

    return cfgGen, xCoord, yCoord


def getCoordinatesFromPoint(inputDir):
    """Read the release point shp file and extract its coordinates

    Checks that only one shp file with only one point exists

    Parameters
    ------------
    inputDir : pathlib Path
        directory to input folder

    Returns
    ------------
    x : float
        x coordinate of release point
    y : float
        y coordinate of release point
    """

    relFile, _, _ = gI.getAndCheckInputFiles(
        inputDir,
        "REL",
        "release point",
        fileExt="shp",
    )
    relPoint = gpd.read_file(relFile)
    geomType = relPoint.geom_type.unique()
    if len(geomType) != 1 and geomType[0] != "Point":
        message = "The shp file %s does not contain a Point geometry type." % relFile
        log.error(message)
        raise ValueError(message)
    if len(relPoint) != 1:
        message = "Provide only one release point in %s!" % relFile
        log.error(message)
        raise ValueError(message)

    point = relPoint.geometry.iloc[0]
    x, y = point.x, point.y
    log.info("release point coordinates are read from %s" % relFile)
    return x, y


def simulateFlowPaths(demDataset, demData, startRow, startCol, perimeter, energyHeight, outputDir, cfgGen):
    """Compute random single flow paths until the number of hit cells reaches the perimeter

    Parameters
    ------------
    demDataset : rasterio dataset
        opened DEM
    demData : dict
        DEM as read by rasterUtils.readRaster (rasterData and header)
    startRow : int
        row index of the release point
    startCol : int
        column index of the release point
    perimeter : float
        maximum number of cells of the deposition area
    energyHeight : float or str
        energy height factor or "elevation" to read it from outputDir/elevation.asc
    outputDir : pathlib Path
        path to the output directory
    cfgGen : configparser section
        GENERAL section of the c2TopRunDF configuration

    Returns
    ------------
    hitCount : numpy array
        number of flow path hits per cell
    """

    mcsMax = cfgGen.getint("mcsmax")
    numLoopSim = cfgGen.getint("numLoopSimulation")
    randomRadius = cfgGen.getfloat("randomRadius")
    denominator = cfgGen.getfloat("denominator")

    demRaster = demData["rasterData"]
    cellSize = demData["header"]["cellsize"]
    nRows = demData["header"]["nrows"]
    nCols = demData["header"]["ncols"]

    # read the energy height raster only once if required
    if not isinstance(energyHeight, float):
        with rasterio.open(outputDir / "elevation.asc") as energyRaster:
            energyHeightRaster = energyRaster.read(1)

    # cells visited by the current single flow path
    flowPathCells = np.zeros_like(demRaster)
    # number of flow path hits per cell
    hitCount = np.zeros_like(demRaster)
    area = 0
    row, col = startRow, startCol

    for _ in range(numLoopSim):
        if area >= perimeter:
            break
        # In order to avoid implausible deposition heights due to an identical starting point, each starting point
        # of a single flow run is determined randomly within a certain radius (around the previous starting point)
        row = np.random.randint(max(0, row - randomRadius), min(nRows, row + randomRadius))
        col = np.random.randint(max(0, col - randomRadius), min(nCols, col + randomRadius))
        position = [row, col]
        flowPathCells.fill(0)
        mcs = 0
        while mcs < mcsMax and position[0] <= nRows - 1 and position[1] <= nCols - 1:
            if position[0] > 0 and position[1] > 0:
                if area >= perimeter:
                    break
                # Adjust energy height dynamically to avoid implausible depo-heights at the start cell.
                # The denominator in the exponent of the decayFactor (default: 100) scales the "range" of the
                # decay. A larger denominator results in slower decay, meaning the decay factor remains
                # significant over longer distances. A smaller denominator causes faster decay, meaning
                # the decay factor approaches zero more quickly.
                distance = np.sqrt((position[0] - row) ** 2 + (position[1] - col) ** 2)
                decayFactor = np.exp(-distance / denominator)
                if isinstance(energyHeight, float):
                    tempHeight = energyHeight * cellSize * decayFactor
                else:
                    tempHeight = energyHeightRaster[position[0], position[1]] * cellSize * decayFactor
                singleFlowPath = randomsfp.MonteCarloSingleFlowPath(demDataset, flowPathCells, position, tempHeight)
                position = singleFlowPath.NextStartCell()
                flowPathCells[position[0], position[1]] = True
                hitCount[position[0], position[1]] += 1
                if hitCount[position[0], position[1]] == 1:
                    area += 1
            else:
                mcs += 1
                position = [row, col]
                flowPathCells.fill(0)

    return hitCount


def computeDepositionHeight(hitCount, volume, perimeter, cellSize, cfgGen):
    """Distribute the input volume on the deposition area

    The normalized hit count is scaled to the mean deposition height, smoothed with a
    diffusion kernel and finally adjusted to match the input volume

    Parameters
    ------------
    hitCount : numpy array
        number of flow path hits per cell (cell [0, 0] is set to 0)
    volume : float
        input volume
    perimeter : float
        maximum number of cells of the deposition area
    cellSize : float
        cell size of the DEM
    cfgGen : configparser section
        GENERAL section of the c2TopRunDF configuration

    Returns
    ------------
    depoHeight : numpy array
        deposition height per cell
    """

    hitCount[0, 0] = 0
    hitNorm = hitCount / np.amax(hitCount)
    meanHeight = volume / perimeter
    volumeFactor = volume / (np.sum(hitNorm) * cellSize ** 2)
    depoHeight = hitNorm * (meanHeight * volumeFactor)

    #############################################################################################
    # Several strategies for distributing the input volume plausibly across the storage area:
    #############################################################################################
    # --A-- # Diffusion algorithm:
    # A diffusion algorithm is a method used to smooth values in a grid or matrix
    # and distribute them more evenly. It simulates the physical process of diffusion,
    # in which material or energy moves from areas of high concentration to areas of low
    # concentration.
    flatKernel = [float(value) for value in cfgGen["kernelMatrixValues"].split(",")]
    shapeKernel = tuple(int(value) for value in cfgGen["kernelMatrixShape"].split(","))
    kernel = np.array(flatKernel).reshape(shapeKernel)
    depoHeight = convolve(depoHeight, kernel, mode="constant", cval=0.0)
    #############################################################################################
    # --B-- # Apply Gaussian smoothing to reduce sharp peaks
    # from scipy.ndimage import gaussian_filter
    # depoHeight = gaussian_filter(depoHeight, sigma=2)
    #############################################################################################
    # --C-- # Deposition height normalized by mean deposition height:
    # depoHeight = depoHeight / np.max(depoHeight) * meanHeight

    # Adjust deposition values to match input volume
    totalDepositedVolume = np.sum(depoHeight) * cellSize ** 2
    if abs(volume - totalDepositedVolume) > 1e-6:
        adjustmentFactor = volume / totalDepositedVolume
        depoHeight *= adjustmentFactor
        log.info("Adjusted deposition values by factor: %s", adjustmentFactor)
    else:
        log.info("Deposition volume matches input volume.")

    return depoHeight


def needsPreprocessing(filePath):
    """Check if the file contains commas as decimal separators

    Parameters
    ------------
    filePath : pathlib Path
        path to raster file

    Returns
    ------------
    bool
        True if the file contains a comma
    """
    with open(filePath, "r", encoding="utf-8") as f:
        with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            return b"," in mm


def preprocessRaster(filePath):
    """Replace commas with periods in numeric values of a raster file

    If preprocessing is required, the result is written to a temporary file
    (filename_temp.asc) next to the input file

    Parameters
    ------------
    filePath : pathlib Path
        path to raster file

    Returns
    ------------
    pathlib Path
        path to the temporary file, or filePath if no preprocessing is needed
    """
    if not needsPreprocessing(filePath):
        return filePath

    tempFile = filePath.with_stem(filePath.stem + "_temp").with_suffix(".asc")

    with open(filePath, "r", encoding="utf-8") as fIn:
        with mmap.mmap(fIn.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            content = mm.read().decode("utf-8")
            updatedContent = content.replace(",", ".")
            # Ensure no extra newlines are introduced
            updatedContent = "\n".join(line.strip() for line in updatedContent.splitlines())

    with open(tempFile, "w", encoding="utf-8") as fOut:
        fOut.write(updatedContent)

    return tempFile


def parseDecimal(inputString):
    """Convert a string to float, accepting a comma as decimal separator

    Parameters
    ------------
    inputString : str
        number as string, e.g. "0.1" or "0,1"

    Returns
    ------------
    float
        parsed number
    """
    if "," in inputString and "." not in inputString:
        inputString = inputString.replace(",", ".")
    try:
        return float(inputString)
    except ValueError:
        message = "Invalid input %s. Please enter a number with a valid decimal separator." % inputString
        log.error(message)
        raise ValueError(message)
