Script-based usage
------------------

Use this option to run DebrisFrame from Python scripts. Unlike the QGIS option,
**script-based execution requires input files in the process-directory 
structure** described in :doc:`workflowIn2DFHyd` (for hydrograph preprocessing)
and `AvaFrame documentation <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#input>`_ (for simulation inputs).

After :doc:`installation`, open a terminal and change to the ``debrisframe``
 directory::

   cd [YOURDIR]/DebrisFrame/debrisframe

Replace ``[YOURDIR]`` with your installation path. Copy ``debrisframeCfg.ini`` to  ``local_debrisframeCfg.ini``
and change the ``avalancheDir`` to your process directory.

Choose one of the following workflows:

* **Run in2DFHyd separately:** Prepare the DEM, hydrograph, cross section and
  levee points, then execute::

     pixi run python runIn2DFHyd.py

  This creates a CSV with hydraulic initial conditions. If you run c1TIF
  separately afterwards, provide this CSV in ``Inputs/REL`` and use a
  time-dependent release without triggering preprocessing a second time.

* **Run c1TIF with automatic hydraulic preprocessing:** Set
  ``inputHydrograph = True`` and ``timeDependentRelease = True`` in the
  relevant c1TIF configuration, then execute::

     pixi run python runC1TIF.py

  c1TIF runs in2DFHyd first and transfers its initial-condition CSV into
  ``Inputs/REL`` before starting the simulation.

* **Run c1TIF without hydraulic preprocessing:** Provide the appropriate
  release input (a release area or an existing time-dependent release CSV),
  set ``inputHydrograph = False`` and execute ``runC1TIF.py``::

     pixi run python runC1TIF.py

For file requirements and configuration options, see :doc:`workflowIn2DFHyd`
and :doc:`workflowC1TIF`. For the alternative route through the QGIS
Processing Toolbox, see :doc:`qgisConnector`.