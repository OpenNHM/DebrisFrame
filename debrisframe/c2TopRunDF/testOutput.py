import avaframe.in2Trans.rasterUtils as rasterUtils

import numpy as np
import pathlib


referencePath = pathlib.Path("../data/debrisTopRun/Reference/depo.asc")
testPath = pathlib.Path(f"../data/debrisTopRun/Outputs/c2TopRunDF/depo.asc")
diffPath = pathlib.Path(f"../data/debrisTopRun/Reference/diff")


refData = rasterUtils.readRaster(referencePath)
testData = rasterUtils.readRaster(testPath)

diff = refData["rasterData"] - testData["rasterData"]

if np.all(np.isclose(refData["rasterData"], testData["rasterData"])):
    print("output is gooood")
else:
    print("output is not close")
    rasterUtils.writeResultToRaster(testData["header"], diff, diffPath)