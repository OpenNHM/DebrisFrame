#!/usr/bin/env python
"""
    Run script for generateTopo in module in3Utils
"""
import logging
import pathlib

# Local imports
from debrisframe.in1Utils import generateTopo as gT
from debrisframe.out1Plot import outTopo as oT
from avaframe.in3Utils import cfgUtils, logUtils


# log file name; leave empty to use default runLog.log
logName = 'generateTopo'

# Load avalanche directory from general configuration file
cfgMain = cfgUtils.getGeneralConfig(nameFile=pathlib.Path("debrisframeCfg.ini"))
debrisDir = cfgMain["MAIN"]["avalancheDir"]
# avalancheDir = cfgMain['MAIN']['avalancheDir']

# Start logging
log = logUtils.initiateLogger(debrisDir, logName)
log.info('MAIN SCRIPT')

# Load input parameters from configuration file
cfg = cfgUtils.getModuleConfig(gT, debrisDir)

# Call main function to generate DEMs
[z, name_ext, outDir] = gT.generateTopo(cfg, debrisDir)

# Plot new topogrpahy
oT.plotGeneratedDEM(z, name_ext, cfg, outDir, cfgMain)
