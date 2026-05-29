"""
@author: Christian Scheidl

(modified by Paula Spannring)
"""

import pathlib
import rasterio
import numpy as np
import geopandas as gpd
import logging
import mmap

from scipy.ndimage import convolve
import matplotlib as mpl

import debrisframe.c2TopRunDF.pyTopRunDFRepo.RandomSingleFlow as randomsfp
from debrisframe.c2TopRunDF.pyTopRunDFRepo.PlotResult import HillshadePlotter

import avaframe.in1Data.getInput as gI
import avaframe.in3Utils.initialiseDirs as iD
import avaframe.in3Utils.initializeProject as initProj
import avaframe.in2Trans.rasterUtils as rasterUtils

# To get a reproduceable result, set the seed:
# np.random.seed(42)

# create local logger under avaframe namespace to use its logging configuration
log = logging.getLogger("avaframe.debrisframe.c2TopRunDF")

# Set global font size for plots
mpl.rcParams["font.size"] = 8  # Set font size to 8
mpl.rcParams["axes.titlesize"] = 12  # Set title font size
mpl.rcParams["axes.labelsize"] = 8  # Set axis label font size
mpl.rcParams["xtick.labelsize"] = 8  # Set x-axis tick font size
mpl.rcParams["ytick.labelsize"] = 8  # Set y-axis tick font size


def c2TopRunDFMain(cfgMain, cfgDebris):

    # 3) try to replace some functions (read in data,...)
    # 4) try to allow computing several scenarios in one run (only for one DEM -> difference to original!!!)

    avaDir = cfgMain["MAIN"]["avalancheDir"]
    # TODO: delete work folder first?
    initProj.cleanSingleAvaDir(avaDir, deleteOutput=False)
    output_dir, dem_file = initializeSimulation(avaDir)

    # get input data
    eventName = cfgDebris["GENERAL"]["name"]
    volume = cfgDebris["GENERAL"].getfloat("volume")
    coefficient = cfgDebris["GENERAL"].getfloat("coefficient")

    # if coordinates do not exist in config file, check if a shp-file with the release point is provided
    if cfgDebris["GENERAL"].get("xKoord") == "" or cfgDebris["GENERAL"].get("yKoord") == "":
        cfgDebris["GENERAL"]["relPointFromShp"] = "True"
    else:
        cfgDebris["GENERAL"]["relPointFromShp"] = "False"
        xKoord = cfgDebris["GENERAL"].getfloat("xKoord")
        yKoord = cfgDebris["GENERAL"].getfloat("yKoord")

    if cfgDebris["GENERAL"]["relPointFromShp"]:
        inputDir = pathlib.Path(avaDir, "Inputs")
        xKoord, yKoord = getCoordinatesFromPoint(inputDir)

    artificial_height = cfgDebris["GENERAL"]["energyHeight"]
    if artificial_height != "elevation":
        artificial_height = parse_decimal(str(artificial_height))

    # Open the DEM file
    # Preprocess the DEM file if necessary
    processed_dem_file = preprocess_raster(dem_file)
    demData = rasterUtils.readRaster(processed_dem_file, noDataToNan=False)
    demDataset = rasterio.open(processed_dem_file)

    band = demData["rasterData"]
    demHeader = demData["header"]
    gridsize = demHeader["cellsize"]
    # Initialize variables
    simarea = volume ** (2 / 3) * coefficient
    perimeter = simarea / gridsize ** 2
    row, col = demDataset.index(xKoord, yKoord)
    band2 = np.copy(band)
    band3 = np.copy(band)
    band3.fill(0)
    area = 0
    mcsmax = cfgDebris["GENERAL"].getint("mcsmax")
    numLoopSim = cfgDebris["GENERAL"].getint("numLoopSimulation")
    randomRadius = cfgDebris["GENERAL"].getfloat("randomRadius")
    nrows = demHeader["nrows"]
    ncols = demHeader["ncols"]
    denominator = cfgDebris["GENERAL"].getfloat("denominator")

    # Flowpath simulation
    for x in range(0, numLoopSim):
        if area >= perimeter:
            break
        else:
            # In order to avoid implausible deposition heights due to an identical starting point, each starting point
            # of a single flow run is determined randomly within a certain radius.
            row = np.random.randint(max(0, row - randomRadius), min(nrows, row + randomRadius))
            col = np.random.randint(max(0, col - randomRadius), min(ncols, col + randomRadius))
            position = [row, col]
            band2.fill(0)
            mcs = 0
            while mcs < mcsmax and position[0] <= nrows - 1 and position[1] <= ncols - 1:
                if position[0] > 0 and position[1] > 0:
                    if area >= perimeter:
                        break
                    else:
                        # Adjust energy height dynamically to avoid unplausible depo-heights at the start cell.
                        # The denominator in the exponent of the decay_factor (default: 100) scales the "range" of the
                        # decay. A larger denominator results in slower decay, meaning the decay factor remains
                        # significant over longer distances. A smaller denominator causes faster decay, meaning
                        # the decay factor approaches zero more quickly.
                        distance = np.sqrt((position[0] - row) ** 2 + (position[1] - col) ** 2)
                        decay_factor = np.exp(-distance / denominator)
                        if isinstance(artificial_height, float):
                            temp_height = artificial_height * gridsize * decay_factor
                        else:
                            artificial_raster_height = rasterio.open(output_dir / "elevation.asc")
                            temp_height = (
                                    artificial_raster_height.read(1)[position[0], position[1]]
                                    * gridsize
                                    * decay_factor
                            )
                            artificial_raster_height.close()
                        obj1 = randomsfp.MonteCarloSingleFlowPath(demDataset, band2, position, temp_height)
                        position = obj1.NextStartCell()
                        band2[position[0], position[1]] = True
                        band3[position[0], position[1]] += 1
                        if band3[position[0], position[1]] == 1:
                            area += 1
                else:
                    mcs += 1
                    position = [row, col]
                    band2.fill(0)

    band3[0, 0] = 0
    max_val = np.amax(band3)
    band3 = band3 / max_val
    meanh = volume / perimeter

    dummy = np.sum(band3)
    diff = volume / (dummy * gridsize ** 2)
    meannew = meanh * diff
    band4 = band3 * meannew
    #############################################################################################
    # Several strategies for distributing the input volume plausibly across the storage area:
    #############################################################################################
    # --A-- # Diffusion algorithm:
    # A diffusion algorithm is a method used to smooth values in a grid or matrix
    # and distribute them more evenly. It simulates the physical process of diffusion,
    # in which material or energy moves from areas of high concentration to areas of low
    # concentration.
    flatKernel = [float(value) for value in cfgDebris["GENERAL"]["kernelMatrixValues"].split(",")]
    shapeKernel = tuple(int(value) for value in cfgDebris["GENERAL"]["kernelMatrixShape"].split(","))
    kernel = np.array(flatKernel).reshape(shapeKernel)
    band4 = convolve(band4, kernel, mode="constant", cval=0.0)
    #############################################################################################
    # --B-- # Apply Gaussian smoothing to reduce sharp peaks
    # from scipy.ndimage import gaussian_filter
    # band4 = gaussian_filter(band4, sigma=2)
    #############################################################################################
    # --C-- # Ablagerungshöhe über mittlere Ablagerungshöhe normiert:
    # band4 = band4 / np.max(band4) * meanh

    # Adjust deposition values to match input volume
    total_deposited_volume = np.sum(band4) * gridsize ** 2
    volume_difference = volume - total_deposited_volume
    if abs(volume_difference) > 1e-6:
        adjustment_factor = volume / total_deposited_volume
        band4 *= adjustment_factor
        log.info(f"Adjusted deposition values by factor: {adjustment_factor}")
    else:
        log.info("Deposition volume matches input volume.")

    # Save the output raster
    out_meta = demDataset.meta.copy()
    demDataset.close()
    out_meta.update({"driver": "AAIGrid", "dtype": "float32"})
    output_raster_path = output_dir / "depo.asc"
    with rasterio.open(output_raster_path, "w", **out_meta) as dest:
        dest.write(band4, 1)
    # Clean up the temporary file if preprocessing was done
    if processed_dem_file != dem_file:
        processed_dem_file.unlink()  # Deletes the temporary file

    log.info(f"Simulation finished")
    # Create an instance of the HillshadePlotter class

    plotter = HillshadePlotter()

    # Generate the plot
    plotter.plot(output_raster_path, dem_file, eventName, output_dir)


def initializeSimulation(avaDir):

    demFile = gI.getDEMPath(avaDir)
    _, outputDir = iD.initialiseRunDirs(avaDir, modName="c2TopRunDF", cleanRemeshedRasters=False)
    return outputDir, demFile


def getCoordinatesFromPoint(inputDir):
    """
    read release point shp file and extract coordinates
    check if only one shp file with only one point exists

    Parameters
    ------------
    inputDir : pathlib Path
        directory to input folder

    Returns
    ------------
    x: float
        x coordinate of release point
    y: float
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
        message = "The shp file %s does not contain a Point geometry type." % (relFile)
        log.error(message)
        raise ValueError(message)
    if len(relPoint) != 1:
        message = "Provide only one release point in %s!" % (relFile)
        log.error(message)
        raise ValueError(message)

    point = relPoint.geometry.iloc[0]
    x, y = point.x, point.y
    log.info("release point coordinates are read from %s" % (relFile))
    return x, y


# Funktion zum Testen ob unterschiedliche Dezimaltrennzeichen in den Rasterdaten vorliegen
def needs_preprocessing(file_path):
    """Check if the file contains commas as decimal separators."""
    with open(file_path, "r", encoding="utf-8") as f:
        with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            return b"," in mm


def preprocess_raster(file_path):
    """Preprocess raster file to replace commas with periods in numeric values."""
    if not needs_preprocessing(file_path):
        return file_path  # Return the original file if no preprocessing is needed

    temp_file = file_path.with_stem(file_path.stem + "_temp").with_suffix(".asc")  # Create a temporary file

    with open(file_path, "r", encoding="utf-8") as f_in:
        # Map the file into memory
        with mmap.mmap(f_in.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            # Read the entire file content
            content = mm.read().decode("utf-8")
            # Replace commas with periods
            updated_content = content.replace(",", ".")
            # Ensure no extra newlines are introduced
            updated_content = "\n".join(line.strip() for line in updated_content.splitlines())

    # Write the updated content to a temporary file
    with open(temp_file, "w", encoding="utf-8") as f_out:
        f_out.write(updated_content)

    return temp_file


# Funktion zur Adaptierung unterschiedlicher Dezimaltrennzeichen für Eingabewerte
def parse_decimal(input_string):
    # Prüfen, ob ein Komma als Dezimaltrennzeichen verwendet wird
    if "," in input_string and "." not in input_string:
        input_string = input_string.replace(",", ".")
    try:
        return float(input_string)
    except ValueError:
        raise ValueError("Invalid input. Please enter a number with a valid decimal separator.")
