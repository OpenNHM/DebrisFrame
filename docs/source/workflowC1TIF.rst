Workflow: Thickness integrated flow (c1TIF)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Runs a thickness integrated debris flow simulation via module :py:mod:`c1TIF`.

Inputs:

* ``DEM layer`` (required) - raster layer.
* ``Release layer(s)`` (optional) - required only if the csv file has no x/y columns.
* ``Time-dependent release values / release geometry`` (optional) - csv file; defines the release
  geometry if it contains x/y columns.

.. note::

    The ``initCondHyd.csv`` produced by the Hydrograph Starting Condition (in2DFHyd) tool can be
    used here as the time-dependent release input.

* ``Secondary release layer`` (optional) - only one is allowed.
* ``Entrainment layer`` (optional) - only one is allowed.
* ``Resistance layer`` (optional) - only one is allowed.
* ``Destination folder`` (required) - process directory.
* ``Expert configuration file`` (advanced, optional) - ``c1TIFCfg.ini``. See
  :ref:`moduleC1TIF:Model configuration`.

Outputs:

* ``Output layer`` - simulation result.

Get default DebrisFrame module ini
-------------------

Extracts the default configuration file for the selected DebrisFrame module. The file can then be
edited and supplied as the expert configuration file when running the corresponding simulation tool.

Inputs:

* ``Module`` (required) - select either ``c1TIF`` or ``in2DFHyd``.
* ``Destination file`` (required) - ini file to write.

Outputs:

* the written ini file.


Relevant parameters
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

    - ``adaptSfcStopped = 1`` (and ``explicitFriction = 1`` -> default = 0) - all particles with flow velocity = 0 are summed to the topography
    - ``adaptSfcEntrainment = 1`` - the topography changes according to entrainment
    - ``entrainableDeposition = True`` - flowing mass re-entrains already deposited or stopped material when it is flowing over it.
    - ``resType = demAdapted|sfcChange`` - get the adapted topography as a result|get the difference between the pre- and post-simulation topography as a result
    - ``rhoEnt`` - density of the entrained material

* The parameter ``frictModel`` modifies the `friction model <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#friction-model>`_.