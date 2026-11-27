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

For file requirements and configuration options, see :doc:`workflowIn2DFHyd`
and :doc:`workflowC1TIF`. For the QGIS usage see :doc:`qgisUsage`.