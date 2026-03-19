"""
    Run script for getting rename dataframe, no actuall renameing is done!
"""

# Load modules
import shutil
import pathlib
import glob
import warnings

# Local imports
from avaframe.in3Utils import cfgUtils
from avaframe.in3Utils import cfgHandling
from avaframe.in3Utils import logUtils

# import computation modules
import debrisframe as debf

# -------------Required settings ------
# which parameters to add to simulation name; sep = ','
csvString = 'xsivoellmy'
# -------------Required settings ------

# log file name; leave empty to use default runLog.log
logName = 'runRenaming'

#  Load general configuration file
modPath = pathlib.Path(debf.__file__).resolve().parent
cfgNameFile = modPath / "debrisframeCfg.ini"
cfgMain = cfgUtils.getGeneralConfig(nameFile=cfgNameFile)
debrisDir = cfgMain['MAIN']['avalancheDir']
# logging
warnings.filterwarnings('ignore')
log = logUtils.initiateLogger(debrisDir, logName)
log.info('MAIN SCRIPT')
log.info('Current avalanche: %s', debrisDir)

debrisDir = pathlib.Path(debrisDir)
# rename
renameDF = cfgHandling.addInfoToSimName(debrisDir, csvString)
oldnameList = list(renameDF['simName'])
newnameList = list(renameDF['newName'])

for name in list(newnameList):
    log.info(name)

sourceDir = debrisDir / 'Outputs'
targetDir = sourceDir / 'renamed'

# test if folder already exists. Otherwise folder is created and files are copied
if targetDir.exists():
    log.info('Target directory already exists')
else:
    targetDir.mkdir(parents=True, exist_ok=True)

    # copy original file and save it in new path
    for i,oldname in enumerate(oldnameList):
        # get files in output directory
        files = glob.glob(str(sourceDir / f'**/{oldname}*.asc'), recursive=True)
        sourcePath = [pathlib.Path(f) for f in files]
        # split filename from old path and assign new path
        newfiles = [f.split("\\")[-1] for f in files]
        newfiles = [f.replace(oldname,newnameList[i]) for f in newfiles]
        targetPath = [targetDir / f for f in newfiles]
        # save copied files in Outputs/renamed
        for i,tgp in enumerate(targetPath):
            shutil.copy2(sourcePath[i],tgp)
            log.info(f"Renamed: {sourcePath[i]} -> {tgp}")

        log.info('Files successfully copied and renamed')












