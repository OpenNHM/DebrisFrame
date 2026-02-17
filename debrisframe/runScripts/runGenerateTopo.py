#!/usr/bin/env python
"""
    Run script for generateTopo in module in3Utils
"""
import pathlib

# Local imports
from debrisframe.in1Utils import generateTopo as gT
from avaframe.out3Plot import outTopo as oT
from avaframe.in3Utils import cfgUtils, logUtils, generateTopo, cfgHandling

if __name__ == '__main__':
    # log file name; leave empty to use default runLog.log
    logName = 'generateTopo'

    # Load avalanche directory from general configuration file
    cfgMain = cfgUtils.getGeneralConfig(nameFile=pathlib.Path("debrisframeCfg.ini"))
    debrisDir = cfgMain["MAIN"]["avalancheDir"]

    # Start logging
    log = logUtils.initiateLogger(debrisDir, logName)
    log.info('MAIN SCRIPT')

    # Load default input parameters from configuration file and update with override parameters
    debrisCfg = cfgUtils.getModuleConfig(gT)
    cfg = cfgUtils.getModuleConfig(generateTopo,onlyDefault=debrisCfg["in3Utils_generateTopo_override"].getboolean("defaultConfig"))
    cfg, debrisCfg = cfgHandling.applyCfgOverride(cfg, debrisCfg, generateTopo, addModValues=False)

    # Call main function to generate DEMs
    [z, name_ext, outDir] = gT.generateTopo(cfg, debrisDir)

    # Plot new topogrpahy
    oT.plotGeneratedDEM(z, name_ext, cfg, outDir, cfgMain)
