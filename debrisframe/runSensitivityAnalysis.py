"""
Sample the input parameters and run the debris flow setup of com1DFA
based on runc1TIF.py
"""

import pathlib
import time
import argparse
import numpy as np
import pandas as pd
from SALib.sample.sobol import sample

# Local imports
# import config and init tools
from avaframe.in3Utils import cfgUtils, logUtils, cfgHandling
import avaframe.in3Utils.initializeProject as initProj
from avaframe.in3Utils import fileHandlerUtils as fU
from avaframe.com1DFA import com1DFA

# import computation modules
import debrisframe as debf
from debrisframe.c1TIF import c1TIF

def hydrograph(qp, tp, tr, tb, n, dt):
    """creates a single- or mulitple-surge hydrograph

    Parameters
    ----------
    qp : int
        peak discharge
    tp : int
        time to peak
    tr : int
        recession time of declining branch
    tb : int
        time between surges
    n  : int
        numer of surges
    dt : int
        time discretization

    Returns
    -------
    time   : list
        time steps
    q  : list
        discharge per timestep
    totVol  : float
        total event-volume
    dV : float
        volume per time interval
    cumVol : float
        cumulative sumline of volume
    hydDF  : dataframe
        hydrograph as dataframe as starting condition
    """

    n = int(n)
    if not isinstance(n, int):
        raise TypeError('input variable n: only integers are allowed!')
    
    paramHyd = {'peak discharge': qp,
                'time to peak': tp,
                'recession time': tr,
                'time between surges': tb}
    
    for param_name, param_value in paramHyd.items():
        if param_value % dt != 0:
            raise ValueError(f'{param_name} must be divisible by dt = {dt}')

    # convert to integers
    tp = int(tp)
    tr = int(tr)
    tb = int(tb)

    # loop over surges

    # duration time of one surge
    td = tp + tr
    # time
    time = np.arange(0,td+1,dt)
    
    # calculation of q
    q = []
    for t in time:
        if t <= tp:
            qt = qp/tp * t

        else:
            t = t - tp
            qt = qp - qp/tr * t
        q.append(qt)

    # multiplying surges
    if n > 1:
        if tb == 0:
            q += (n - 1) * q[1:]
        
        else:
            tb = tb // dt - 1 
            zeros = [0] * tb
            qi = q[:-1] + zeros
            qi += (n - 2) * qi[1:]
            qi += q[1:]
            q = qi

        # time = np.arange(0, n * td + (n - 1) * tb + dt, dt)
        time = np.arange(0, len(q) * dt, dt)

    # calculation of total event volume
    totVol = 0.5 * qp * (tp + tr) * n
    # calclulation of Volume per time interval
    dV = [(q[x+1] + q[x]) * 0.5 * dt for x in range(len(q)-1)]
    dV = np.array(dV)
    # calculation of cumulative sumline of volume
    cumVol = np.cumsum(dV)

    # calculate release thickness
    def relTh(volume): #TODO: exclude es separate function
        return np.round(0.0128 * volume, 3)   
    relThVal = relTh(dV)

    # calculation of flow velocity (Rickenmann 1999)
    s = 0.81 # slope
    vel = [2.1 * ((q[x+1] + q[x]) * 0.5)**0.33 * s ** 0.33
       for x in range(len(q)-1)]
    vel = np.round(np.array(vel),1)

    # save hydrograph in a csv-file
    hydDF = pd.DataFrame({'timestep': time[:-1], 'thickness': relThVal, 'velocity': vel})


    return time, q, totVol, dV, cumVol, hydDF

def runSensitivityAnalysis():
    """Run com1DFA in parallel with sampled debris flow parameters for SA
    For the SA the variance-based method by Sobol is used (https://doi.org/10.1016/S0378-4754(00)00270-6)
    For the parameter sampling Saltelli's extension of the Sobol sequence is used (https://doi.org/10.1016/S0010-4655(02)00280-1)
    The functions needed for parameter sampling and executing the SA are included in the SALib (https://doi.org/10.5281/zenodo.17330349)

    Parameters
    ----------
    debrisDir: str
        path to debris flow directory (setup e.g. with init scripts)

    Returns
    -------
    peakFilesDF: pandas dataframe
        with info about com1DFA peak file locations
    """

    # Time the whole routine
    startTime = time.time()

    # log file name; leave empty to use default runLog.log
    logName = "runSensitivityAnalysis"

    # Load debris flow directory from general configuration file
    modPath = pathlib.Path(debf.__file__).resolve().parent
    cfgNameFile = modPath / "debrisframeCfg.ini"
    cfgMain = cfgUtils.getGeneralConfig(nameFile=cfgNameFile)
    debrisDir = cfgMain["MAIN"]["avalancheDir"]

    # Start logging
    log = logUtils.initiateLogger(debrisDir, logName)
    log.info("MAIN SCRIPT")
    log.info("Current debris flow: %s", debrisDir)

    # Parameter sampling #TODO: separate function
    log.info("start parameter sampling")
    # Sobol-Saltelli-sampling
    # Define the model inputs, example on Voellmy
    paramNameFric = ['muvoellmy', 'xsivoellmy'] #TODO: definition for all friction models
    paramNameHyd = list(hydrograph.__code__.co_varnames[:hydrograph.__code__.co_argcount])[:-1]
    problem = {
        'num_vars': 7, #TODO: parameter
        'names': paramNameFric + paramNameHyd,
        'bounds': [[0.001, 0.600], #TODO: parameter
                [0, 2000],
                [8, 90],
                [2, 22],
                [8, 96],
                [0, 300],
                [0, 40]
                ]
    }

    number = 4 #TODO: parameter
    calcSecondOrder = False #TODO: parameter    
    sampleParam = sample(problem, number, calc_second_order=calcSecondOrder,scramble=True, seed=8765)
    sampleParam = np.unique(sampleParam, axis=0) #TODO: does not recognize floats with really small deviations in last digits
    #TODO: for memory/performance reasons only store unique values?

    paramsFric = {}
    for i, p in enumerate(paramNameFric):
        paramsFric[p] = '|'.join(str(x) for x in sampleParam[:, i])
    
    # make hydrograph parameters divisible by dt
    dt = 2 #TODO: parameter
    s = len(paramNameFric)
    for i in range(s, s + len(paramNameHyd) - 1): #TODO: optimize code
        sampleParam[:, i] = sampleParam[:, i] - sampleParam[:, i] % dt
    print(sampleParam)

    log.info("start generating hydrograph files")
    
    # save input hydrographs as csv-files in REL-folder
    debrisDir = pathlib.Path(debrisDir)
    inputsDir = debrisDir / "Inputs" / "REL"
    for i, s in enumerate(sampleParam):
        qp, tp, tr, tb, n = s[2:] #TODO: include in function --> dependency on paramNameHyd
        *_, hydDF = hydrograph(qp, tp, tr, tb, n, dt)
        hydDF.to_csv(inputsDir / f'release{i}.csv',sep=',', header=True, index=False) #TODO: naming
    

    
    # # starting simulations
    # # ----------------
    # # Clean input directory(ies) of old work files
    # initProj.cleanSingleAvaDir(debrisDir, deleteOutput=False)

    # # load debris flow config
    # debrisCfg = cfgUtils.getModuleConfig(c1TIF)
    # # insert sampled parameters
    # for p in paramsFric.keys():
    #     debrisCfg["com1DFA_com1DFA_override"][p] = paramsFric[p]

    # # perform com1DFA simulation with debris flow settings
    # # get comDFA configuration and update with debris flow parameter set
    # com1DFACfg = cfgUtils.getModuleConfig(
    #     com1DFA,
    #     fileOverride="",
    #     modInfo=False,
    #     toPrint=False,
    #     onlyDefault=debrisCfg["com1DFA_com1DFA_override"].getboolean("defaultConfig"),
    # )
    # com1DFACfg, debrisCfg = cfgHandling.applyCfgOverride(
    #     com1DFACfg, debrisCfg, com1DFA, addModValues=False
    # )

    # # run the com1DFA module with debris flow settings
    # dem, plotDict, reportDictList, simDF = com1DFA.com1DFAMain(
    #     cfgMain, cfgInfo=com1DFACfg
    # )

    # # print info about simulation performed to log
    # log.info("Com1DFA run performed with debris flow settings")

    # # Get peakfiles to return to QGIS
    # debrisDir = pathlib.Path(debrisDir) #TODO: duplicate
    # inputDir = debrisDir / "Outputs" / "com1DFA" / "peakFiles"
    # peakFilesDF = fU.makeSimDF(inputDir, avaDir=debrisDir)

    # # Print time needed
    # endTime = time.time()
    # log.info("Took %6.1f seconds to calculate." % (endTime - startTime))

    # #TODO: disable plotting of results

    # return peakFilesDF

if __name__ == "__main__":

    runSensitivityAnalysis()
        
