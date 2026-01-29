import rasterio
import time
import numpy as np
from testClass import RasterioClass


rasterPath = "../data/debrisTopRun/Inputs/topofan.asc"

rasterTopRun = rasterio.open(rasterPath)
rasterAvaFrame = rasterTopRun.read(1)

timeArrayTopRun = np.empty(0)
timeArrayAvaFrame = np.empty(0)


for i in range(10000):
    # TopRun

    startTimeTopRun = time.time()

    classTR = RasterioClass(rasterTopRun)
    heightTR = classTR.topRun()

    endTimeTopRun = time.time()
    timeArrayTopRun = np.append(timeArrayTopRun, endTimeTopRun - startTimeTopRun)

    # AvaFrame
    startTimeAvaFrame = time.time()

    classAF = RasterioClass(rasterAvaFrame)
    heightAF = classAF.avaframe()

    endTimeAvaFrame = time.time()
    timeArrayAvaFrame = np.append(timeArrayAvaFrame, endTimeAvaFrame - startTimeAvaFrame)


print("TopRun: Took %6.1f seconds to calculate." % (np.sum(timeArrayTopRun)))
print("AvaFrame: Took %6.1f seconds to calculate." % (np.sum(timeArrayAvaFrame)))


print(f"TopRun Average / AvaFrame Average: {np.mean(timeArrayTopRun) / np.mean(timeArrayAvaFrame)}")

print(f"TopRun Average / AvaFrame Average per Read: {np.mean(timeArrayTopRun) / np.mean(timeArrayAvaFrame) / 6}")
print("result TopRun", heightTR)
print("result AvaFrame", heightAF)