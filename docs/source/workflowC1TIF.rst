Workflow: c1TIF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Runs a thickness integrated debris-flow simulation via module :py:mod:`c1TIF`
with a debris-flow hydrograph starting condition.

Choosing the execution workflow
-------------------------------

There are two ways to run ``c1TIF``:

* **Script-based usage:** Prepare the input files in the DebrisFrame project  `folder structure <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#input>`_
  and run ``runC1TIF.py``. To generate the hydrograph-based starting condition
  automatically, set ``inputHydrograph = True`` in ``local_c1TIFCfg.ini``. The ``in2DFHyd``
  preprocessing step is then executed as part of the simulation.
* **QGIS usage:** Load or create the required input layers in the QGIS project and
  select them in the ``Thickness integrated flow (c1)`` processing tool. The files do **not** need to be placed in
  the separate input-folder structure used by the script-based workflow. When using a
  hydrograph-based starting condition, first run ``Hydrograph Starting Condition (in2DFHyd)`` separately in QGIS, then
  select its generated CSV file as the time-dependent release input for ``Thickness integrated flow (c1)``.

For the preparation of hydrograph input data, see :doc:`workflowIn2DFHyd`.

Input data
-----------------------

Between the following inputs can be selected:

* ``DEM layer`` (required) - raster layer.
* ``Release layer(s)`` (optional) - required only if the csv file has no x/y columns or if ``timeDependentRelease = False``.
* ``Time-dependent release values / release geometry`` (optional) - csv file; defines the release
  geometry if it contains x/y columns.

.. note::

    The ``initCondHyd.csv`` produced by the Hydrograph Starting Condition (in2DFHyd) tool can be
    used here as the time-dependent release input.

* ``Secondary release layer`` (optional) - only one is allowed.
* ``Entrainment layer`` (optional) - only one is allowed.
* ``Resistance layer`` (optional) - only one is allowed.
* ``Destination folder`` (optional) - process directory.
* ``Expert configuration file`` (advanced, optional) - ``c1TIFCfg.ini``. See
`AvaFrame documentation <https://docs.avaframe.org/en/latest/advancedUsage.html#via-the-cfgs-directory>`_.

Model configuration
-----------------------

The model configuration is read from a configuration file: ``c1TIF/c1TIFCfg.ini``. In this file,
all model parameters are listed and can be modified (see `com1DFA documentation <https://docs.avaframe.org/en/latest/moduleCom1DFA.html>`_).
These parameters overwrite the respective parameters of AvaFrame's ``com1DFACfg.ini``
and DebrisFrame's ``in2DFHydCfg.ini`` configuration file.

**Script-based usage:** We recommend to create a local copy
and keep the default configuration in ``c1TIF/c1TIFCfg.ini`` untouched.
For this purpose, in ``DebrisFrame/debrisframe/`` run:::

    cp c1TIF/c1TIFCfg.ini c1TIF/local_c1TIFCfg.ini

and modify the parameter values in there.

**QGIS usage:** The ``Get default module ini`` tool extracts the
default configuration file for the selected DebrisFrame module. The file
can then be edited and supplied as the expert configuration file
when running the corresponding simulation tool.

Inputs:

* ``Module`` (required) - select either ``c1TIF`` or ``in2DFHyd``.
* ``Destination file`` (required) - ini file to write.

Outputs:

* the written ini file.


Output data
-----------------

For script-based usage, the simulation results are saved to: *Outputs/com1DFA*.
The description of the default and optional results are in the
`AvaFrame documentation <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#output>`_.
For QGIS, the output layers are automatically loaded in the QGIS project.

Relevant parameters
-------------------

Basically, the meaning of the single parameters in ``c1TIF/c1TIFCfg.ini`` is explained in the `AvaFrame <https://docs.avaframe.org/en/latest/index.html>`_ and
this documentation.
However, the following are especially relevant because they control the workflow for :py:mod:`c1TIF`.

* **Script-based usage:** To select the hydrograph starting condition for :py:mod:`c1TIF`,
  set ``inputHydrograph = True`` (with ``timeDependentRelease = True``, the default).
  This calls ``in2DFHyd`` to compute the starting condition automatically.
  The section ``[in2DFHyd_in2DFHyd_override]`` of the configuration file contains
  the module-specific parameters. For details, see :ref:`moduleIn2DFHyd:Model configuration`.
* **QGIS usage:** Run ``in2DFHyd`` separately and supply its output CSV file as the
  time-dependent release input of ``c1TIF``. Keep ``inputHydrograph = False``; the
  hydrograph preprocessing must not be started automatically in this workflow.
* If ``timeDependentRelease = False``, the starting condition is instead calculated from
  a `release area <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#input>`_ and
  a constant thickness released at timestep 0 (see `AvaFrame docu <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#release-entrainment-thickness-settings>`_).


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