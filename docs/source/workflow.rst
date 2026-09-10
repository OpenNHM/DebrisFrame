Workflow
=========

There are several ways to execute the different modules that DebrisFrame provides.
In the following sections, we give some advice on how to get started with DebrisFrame.

Script-based application
------------------------

After the `installation of DebrisFrame <https://docs.debrisframe.org/en/latest/installation.html#>`_
make sure you change to your ``DebrisFrame`` directory by::

  cd [YOURDIR]/DebrisFrame/data/[DEBRIS]

Replace ``[YOURDIR]`` and ``[DEBRIS]`` with the directory from your installation step and your
debris-flow directory, respectively.

Make sure you have all the input data you need to run the modules you want to execute (`c1TIF <file:///C:/Users/jlahrssen/DebrisFrame/docs/_build/html/moduleC1TIF.html>`_,
:ref:`moduleIn2TopoHyd:Input`).

If desired, you can modify the configuration settings as described in :ref:`moduleC1TIF:Model configuration`.

Then run ::

  pixi run python runC1TIF.py


Application via QGIS
---------------------

.. Note:: 
    This documentation will be added soon!


Relevant parameters
-------------------

Basically, the meaning of the single parameters in ``c1TIF/c1TIFCfg.ini`` is explained in the `AvaFrame <https://docs.avaframe.org/en/latest/index.html>`_ and
`DebrisFrame <https://docs.debrisframe.org/en/latest/index.html>` documentation.
However, the following ones are especially relevant because they control the workflow for :py:mod:`c1TIF`.

* To select the Hydrograph starting condition for :py:mod:`c1TIF`, set ``inputHydrograph = True`` (and ``timeDependentRelease = True`` -> default).
  This setting uses the ``in2TopoHyd`` module to compute the starting condition.
  The section ``[in2TopoHyd_in2TopoHyd_override]`` of the configuration file lists the specific parameters for the module.
  Detailed information about these parameters can be found in :ref:`moduleIn2TopoHyd:Model configuration`.
  If ``timeDependentRelease`` is set to ``False``, the starting condition is calculated from a `release area <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#input>`_.


* The mesh resolution for the simulation can be specified using ``meshCellSize`` (default: 2 m).


* When `entrainment <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#entrainment>`_ and `detrainment <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#detrainment>`_ processes or
  stopping (flow velocity = 0) are taken into account, the ground surface changes as well. In order to allow an `adaptive surface <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#adaptive-surface>`_ during your simulation,
  following settings are recommended:

    - ``adaptSfcStopped = 1`` (and ``explicitFriction = 1`` -> default = 0) - all particles with flow velocity = 0 are summed to the topography
    - ``adaptSfcEntrainment = 1`` - the topography changes according to entrainment
    - ``entrainableDeposition = True`` - flowing mass re-entrains already deposited or stopped material when it is flowing over it.
    - ``resType = demAdapted`` - get the adapted topography as a result
    - ``restType = sfcChange`` - get the difference between the pre- and post-simulation topography as a result
    - ``rhoEnt`` - density of the entrained material

* The parameter ``frictModel`` modifies the `friction model <https://docs.avaframe.org/en/latest/theoryCom1DFA.html#friction-model>`_.

