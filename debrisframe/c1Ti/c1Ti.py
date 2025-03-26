"""
    Debris flow overrides for com1DFA
"""

# Load modules
import logging


# Local imports
from avaframe.in3Utils import cfgUtils
from avaframe.in3Utils import cfgHandling
from avaframe.com1DFA import com1DFA

# create local logger
# change log level in calling module to DEBUG to see log messages
log = logging.getLogger(__name__)


def c1TiMain(cfgMain, debrisCfg):
    """Run and adjust parameters to match debris flow settings for com1DFA run,
    result files, reports and plots are saved analog to a standard com1DFA model run

    Parameters
    -----------
    cfgMain: configparser object
        main DebrisFrame settings
    debrisCfg: configparser object
        configuration settings for debris flow including com1DFA override parameters

    """

    # ++++++++++ set configurations for com1DFA and override ++++++++++++
    # get comDFA configuration and update with debris flow parameter set
    com1DFACfg = cfgUtils.getModuleConfig(
        com1DFA,
        fileOverride="",
        modInfo=False,
        toPrint=False,
        onlyDefault=debrisCfg["com1DFA_com1DFA_override"].getboolean("defaultConfig"),
    )
    com1DFACfg, debrisCfg = cfgHandling.applyCfgOverride(
        com1DFACfg, debrisCfg, com1DFA, addModValues=False
    )

    # run the com1DFA module with debris flow settings
    dem, plotDict, reportDictList, simDF = com1DFA.com1DFAMain(
        cfgMain, cfgInfo=com1DFACfg
    )

    # print info about simulation performed to log
    log.info("Com1DFA run performed with debris flow settings")

    return dem, plotDict, reportDictList, simDF
