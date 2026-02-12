"""
    Simple plotting for DEMs
"""

import logging

# local imports
from avaframe.in3Utils import geoTrans
import avaframe.out3Plot.plotUtils as pU
import avaframe.out3Plot.outTopo as oT

# create local logger
log = logging.getLogger("avaframe.debrisframe.out1Plot")

def plotGeneratedDEM(z, nameExt, cfg, outDir, cfgMain):
    """ Plot DEM with given information on the origin of the DEM """

    cfgTopo = cfg['TOPO']
    cfgDEM = cfg['DEMDATA']

    # input parameters
    dx = float(cfgTopo['dx'])
    xl = float(cfgDEM['xl'])
    yl = float(cfgDEM['yl'])
    demName = cfgDEM['demName']

    # Set coordinate grid with given origin
    nrows, ncols = z.shape
    X, Y = geoTrans.makeCoordinateGrid(xl, yl, dx, ncols, nrows)

    topoNames = {'IP': 'inclined Plane', 'FP': 'flat plane', 'PF': 'parabola flat', 'TPF': 'triple parabola flat',
                 'HS': 'Hockeystick smoothed', 'BL': 'bowl', 'HX': 'Helix', 'PY': 'Pyramid', 'DFTA': 'generic debris-flow topography'}

    ax, fig = oT._generateDEMPlot(X, Y, z, topoNames[nameExt])

    # Save figure to file
    outName = '%s_%s_plot' % (demName, nameExt)
    # save and or show figure
    plotPath = pU.saveAndOrPlot({'pathResult': outDir}, outName, fig)
    log.info('Saving plot to: %s', plotPath)

