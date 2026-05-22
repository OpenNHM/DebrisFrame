"""
Run conversion from thickness to depth using DEM
"""

import pathlib

# Local imports
import avaframe.in2Trans.rasterUtils as IOf
from avaframe.in1Data import getInput as gI
import avaframe.in2Trans.transformFields as tF
import avaframe.out3Plot.outTransformPlots as oT
from avaframe.in3Utils import fileHandlerUtils as fU
from avaframe.in3Utils import cfgUtils

import debrisframe as debf


def runD2Th(debrisDir, comMod, resType, profileAxis, profileIndex):
    # fetch dem
    dem = gI.readDEM(debrisDir)

    # directory with peak files
    inDir = pathlib.Path(debrisDir, "Outputs", comMod, "peakFiles")
    resFiles = list(inDir.glob("*_%s.asc" % resType)) + list(inDir.glob("*_%s.tif" % resType))

    # create output directory
    outDir = pathlib.Path(debrisDir, "Outputs", comMod, "peakFiles", "transformed")
    fU.makeADir(outDir)

    # loop over resType files found
    for rF in resFiles:
        # read depth field to dict
        thicknessField = IOf.readRaster(rF)

        # convert depth to thickness using dem
        depthDict, thicknessRasterResized, slopeAngleField = tF.convertDepthThickness(thicknessField, dem, typeOfInput='thickness')

        pName = rF.stem.split("_%s" % resType)[0] + "depth" + "_%s" % resType

        # create plot
        oT.plotDepthToThickness(
            thicknessRasterResized,
            depthDict["rasterData"],
            slopeAngleField,
            profileAxis,
            profileIndex,
            outDir,
            pName,
        )

        # write thickness to file
        outFile = outDir / pName
        IOf.writeResultToRaster(depthDict["header"], depthDict["rasterData"], outFile, flip=True)


if __name__ == "__main__":
    # +++++++++REQUIRED+++++++++++++
    # log file name; leave empty to use default runLog.log
    logName = "runDepthToThickness"
    comMod = "com1DFA"
    resType = "FT"
    profileAxis = "x"
    profileIndex = None
    # ++++++++++++++++++++++++++++++

    # fetch input directory
    # cfgMain = cfgUtils.getGeneralConfig()
    # debrisDir = cfgMain["MAIN"]["avalancheDir"]

    modPath = pathlib.Path(debf.__file__).resolve().parent
    cfgNameFile = modPath / "debrisframeCfg.ini"
    cfgMain = cfgUtils.getGeneralConfig(nameFile=cfgNameFile)
    debrisDir = cfgMain["MAIN"]["avalancheDir"]

    # call conversion
    runD2Th(debrisDir, comMod, resType, profileAxis, profileIndex)
