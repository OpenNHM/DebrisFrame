"""
  Create generic/idealised topographies
"""

# load modules
import logging
import numpy as np
from scipy.stats import norm
import pathlib

# local imports
import avaframe.in3Utils.generateTopo as genTop 

# create local logger
# change log level in calling module to DEBUG to see log messages
log = logging.getLogger("avaframe.debrisframe.in1Utils")

def debrisFlowTopoAverage(cfg):
    """
    Compute coordinates of an average parabolic-shaped slope as a generic topography for debris-flow simulations
    defined by a 2nd-degree polynomial: ax**2 + bx + c
    The parameters of the polynomial function are derived from real watershed profiles (Kessler 2019)
    
    Parameters
    ----------------------
    cfg: configparser Object
        configuration setup for topo generation
    """
    # input parameters
    C = cfg["TOPO"].getfloat("C")
    cff = cfg["CHANNELS"].getfloat("cff")
    cRadius = cfg["CHANNELS"].getfloat("cRadius")
    cInit = cfg["CHANNELS"].getfloat("cInit")
    cMustart = cfg["CHANNELS"].getfloat("cMustart")
    cMuend = cfg["CHANNELS"].getfloat("cMuend")

    # Get grid definitons
    dx, xEnd, yEnd = genTop.getGridDefs(cfg)

    # Compute coordinate grid
    xv, yv, zv, x, y, nRows, nCols = genTop.computeCoordGrid(dx, xEnd, yEnd)

    # If a channel shall be introduced
    # Get parabola Parameters
    [A, B, fLen] = genTop.getParabolaParams(cfg)

    # Set surface elevation
    mask = np.zeros(np.shape(xv))
    mask[np.where(xv < fLen)] = 1 
    zv = (A * xv ** 2 + B * xv + C) * mask

    # If a channel shall be introduced
    if cfg["TOPO"].getboolean("channel"):
        # Compute cumulative distribution function - c1 for upper part (start)
        # of channel and c2 for lower part (end) of channel
        c1 = norm.cdf(xv, cMustart * fLen, cff)
        c2 = 1.0 - norm.cdf(xv, cMuend * fLen, cff)

        # combine both into one function separated at the the middle of
        #  the channel longprofile location
        mask_c1 = np.zeros(np.shape(xv))
        mask_c1[np.where(xv < (fLen * (0.5 * (cMustart + cMuend))))] = 1
        c0 = c1 * mask_c1

        mask_c2 = np.zeros(np.shape(xv))
        mask_c2[np.where(xv >= (fLen * (0.5 * (cMustart + cMuend))))] = 1
        c0 = c0 + c2 * mask_c2

        # Is the channel of constant width or narrowing
        if cfg["TOPO"].getboolean("narrowing"):
            # upper part of channel: constant width
            mask_c1 = np.zeros(np.shape(xv))
            mask_c1[np.where(xv < (fLen * (0.5 * (cMustart + cMuend))))] = 1
            cExtent_c1 = np.zeros(np.shape(xv)) + cRadius

            # lower part of channel: narrowing
            mask_c2 = np.zeros(np.shape(xv))
            mask_c2[np.where(xv >= (fLen * (0.5 * (cMustart + cMuend))))] = 1
            cExtent_c2 = cInit * (1 - c0[:]) + (c0[:] * cRadius)
            
            cExtent = cExtent_c1 * mask_c1 + cExtent_c2 * mask_c2
        else:
            cExtent = np.zeros(np.shape(xv)) + cRadius

        # Set surface elevation
        mask = np.zeros(np.shape(y))
        mask[np.where(abs(y) < cExtent)] = 1
        # Add surface elevation modification introduced by channel
        if cfg["TOPO"].getboolean("topoAdd"):
            zv = zv + cRadius * c0 * (1.0 - np.sqrt(np.abs(1.0 - (np.square(y) / (cExtent ** 2))))) * mask # changed from cExtent to cRadius
            # outside of the channel, add layer of channel thickness
            mask = np.zeros(np.shape(y))
            mask[np.where(abs(y) >= cExtent)] = 1
            mask_c2 = np.ones(np.shape(xv)) #added, smooth transition from upper to lower part of channel
            c0 = c2 * mask_c2 #added to extend lower distribution to upper edge of topography
            zv = zv + cRadius * mask * c0 # changed from cExtent to cRadius
        else:
            zv = zv - cExtent * c0 * np.sqrt(np.abs(1.0 - (np.square(y) / (cExtent ** 2)))) * mask

    # Log info here
    log.info("Generic debris-flow topography is computed")

    return x, y, zv

def generateTopo(cfg, debrisDir):
    """  
    Compute coordinates of desired topography with given inputs  
        
    Parameters  
    ----------------------  
    cfg: configparser Object  
        configuration setup for topo generation  
    debrisDir: string  
        directory to data folder  
    """ 

    # Which DEM type
    demType = cfg["TOPO"]["demType"]

    log.info("DEM type is set to: %s" % demType)

    # Set Output directory
    outDir = pathlib.Path(debrisDir, "Inputs")
    if outDir.is_dir():
        log.info("The new DEM is saved to %s" % (outDir))
    else:
        log.error(
            "Required folder structure: NameOfDebrisFlow/Inputs missing! \
                    Run runInitializeProject first!"
        )

    # Call topography type
    if demType == "FP":
        [x, y, z] = genTop.flatplane(cfg)

    elif demType == "IP":
        [x, y, z] = genTop.inclinedplane(cfg)

    elif demType == "PF":
        [x, y, z] = genTop.parabola(cfg)

    elif demType == "TPF":
        [x, y, z] = genTop.parabolaRotation(cfg)

    elif demType == "HS":
        [x, y, z] = genTop.hockey(cfg)

    elif demType == "BL":
        [x, y, z] = genTop.bowl(cfg)

    elif demType == "HX":
        [x, y, z] = genTop.helix(cfg)

    elif demType == "PY":
        [x, y, z] = genTop.pyramid(cfg)

    elif demType == "DFTA":
        [x, y, z] = debrisFlowTopoAverage(cfg)

    # If a drop shall be introduced
    if cfg["TOPO"].getboolean("drop"):
        z = genTop.addDrop(cfg, x, y, z)

    # moves topo in z direction
    if cfg["DEMDATA"]["zEdit"] != "":
        z = z + cfg["DEMDATA"].getfloat("zEdit")
        log.info("Changed topo elevation by %.2f" % cfg["DEMDATA"].getfloat("zEdit"))

    # Write DEM to file
    genTop.writeDEM(cfg, z, outDir)

    return (z, demType, outDir)
