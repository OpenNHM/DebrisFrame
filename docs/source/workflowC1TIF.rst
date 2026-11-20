Workflow: Thickness integrated flow (c1TIF)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Runs a thickness integrated debris-flow simulation via module :py:mod:`c1TIF`.

Choosing the execution workflow
-------------------------------

There are two ways to run ``c1TIF``:

* **Script-based usage:** Prepare the input files in the DebrisFrame project folder structure
  and run ``runC1TIF.py`` (see :ref:`moduleC1TIF:Input`). To generate the hydrograph-based starting condition
  automatically, set ``inputHydrograph = True`` in ``c1TIFCfg.ini``. The ``in2DFHyd``
  preprocessing step is then executed as part of the simulation.
* **QGIS application:** Load or create the required input layers in the QGIS project and
  select them in the ``c1TIF`` processing tool. The files do **not** need to be placed in
  the separate input-folder structure used by the script-based workflow. When using a
  hydrograph-based starting condition, first run ``in2DFHyd`` separately in QGIS, then
  select its generated CSV file as the time-dependent release input for ``c1TIF``.
  Keep ``inputHydrograph = False`` for this workflow to avoid triggering the automatic
  preprocessing step again.

For the preparation of hydrograph input data, see :doc:`moduleIn2DFHyd` and :doc:`workflowIn2DFHyd`.

1. Prepare the input data
-----------------------

**Script-based usage:** c1TIF simulations are performed within a process directory, organized with the
folder structure described in the `AvaFrame documentation <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#input>`_.
Regarding the release- and entrainment thickness settings we refer to the
`respective AvaFrame section <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#release-entrainment-thickness-settings>`_.

**QGIS application:** The separate folder structure is **not required**.
Load the DEM and hydrograph directly into the QGIS workflow, and select
the corresponding inputs in the ``c1TIF`` tool interface.

2. Model configuration
-----------------------

The model configuration is read from a configuration file: ``c1TIF/c1TIFCfg.ini``. In this file,
all model parameters are listed and can be modified (see :doc:`moduleC1FIF`).
These parameters overwrite the respective parameters of AvaFrame's ``com1DFACfg.ini``
and DebrisFrame's ``in2DFHydCfg.ini`` configuration file.

**Script-based usage:** We recommend to create a local copy
and keep the default configuration in ``c1TIF/c1TIFCfg.ini`` untouched.
For this purpose, in ``DebrisFrame/debrisframe/`` run:

  ::

    cp c1TIF/c1TIFCfg.ini c1TIF/local_c1TIFCfg.ini

and modify the parameter values in there.

**QGIS application:** The ``Get default module ini`` tool extracts the
default configuration file for the selected DebrisFrame module. The file
can then be edited and supplied as the expert configuration file
when running the corresponding simulation tool.

Inputs:

* ``Module`` (required) - select either ``c1TIF`` or ``in2DFHyd``.
* ``Destination file`` (required) - ini file to write.

Outputs:

* the written ini file.


3. Output data
-----------------

For script-based usage, the simulation results are saved to: *Outputs/com1DFA*.
The description of the default and optional results are in the
`AvaFrame documentation <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#output>`_.
For QGIS, the output layers are automatically loaded in the QGIS project.

4. Relevant parameters
-------------------

Basically, the meaning of the single parameters in ``c1TIF/c1TIFCfg.ini`` is explained in the `AvaFrame <https://docs.avaframe.org/en/latest/index.html>`_ and
this documentation.
However, the following ones are especially relevant because they control the workflow for :py:mod:`c1TIF`.

* To select the Hydrograph starting condition for :py:mod:`c1TIF`, set ``inputHydrograph = True`` (and ``timeDependentRelease = True`` -> default).
  This setting uses the ``in2DFHyd`` module to compute the starting condition.
  The section ``[in2DFHyd_in2DFHyd_override]`` of the configuration file lists the specific parameters for the module.
  Detailed information about these parameters can be found in :ref:`moduleIn2DFHyd:Model configuration`.
  If ``timeDependentRelease`` is set to ``False``, the starting condition is calculated from a `release area <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#input>`_.


* The mesh resolution for the simulation can be specified using ``meshCellSize`` (default: 2 m).


* When `entrainment <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#entrainment>`_ and `detrainment <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#detrainment>`_ processes or
  stopping (flow velocity = 0) are taken into account, the ground surface changes as well. In order to allow an `adaptive surface <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#adaptive-surface>`_ during your simulation,
  following settings are recommended:

    - ``adaptSfcStopped = 1``- all particles with flow velocity = 0 are summed to the topography
    - ``adaptSfcEntrainment = 1`` - the topography changes according to entrainment
    - ``entrainableDeposition = True`` - flowing mass re-entrains already deposited or stopped material when it is flowing over it.
    - ``resType = demAdapted|sfcChange`` - get the adapted topography as a result|get the difference between the pre- and post-simulation topography as a result
    - ``rhoEnt`` - density of the entrained material

* The parameter ``frictModel`` modifies the `friction model <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#friction-model>`_.