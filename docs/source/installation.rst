Install DebrisFrame
---------------------

From PyPI
^^^^^^^^^

::

  pip install debrisframe

This installs AvaFrame (``avaframe>=2.2``) as a dependency.

From source
^^^^^^^^^^^
  
Running DebrisFrame means running AvaFrame's com1DFA with parameters for debris flows (:py:mod:`c1TIF`).
Therefore, follow AvaFrame's `installation instructions <https://docs.avaframe.org/en/latest/complexUsage.html>`_ first.

When you have setup AvaFrame you may copy the DebrisFrame repository in the same directory
where you have installed AvaFrame in the previous step (``[YOURDIR]``). Afterwards, change into the DebrisFrame repository.

::

  cd [YOURDIR]
  git clone https://github.com/OpenNHM/DebrisFrame.git
  cd DebrisFrame


Try a first run:

change into your ``debrisframe`` directory (replace ``[YOURDIR]`` with your path from the installation steps)

::

  cd [YOURDIR]/DebrisFrame/debrisframe
  pixi run python runC1TIF.py


.. _installationFromQGis:

From QGIS
^^^^^^^^^

DebrisFrame can be run from QGIS via the OpenNHMQGisConnector plugin. The plugin
installs the required Python packages into QGIS's Python environment and adds
the DebrisFrame modules in the QGIS Processing Toolbox. The DebrisFrame tools only
show up if the ``debrisframe`` package is actually installed in QGIS's Python
environment.

Install the connector
"""""""""""""""""""""

The connector is available from the official QGIS plugin repository
(`plugins.qgis.org <https://plugins.qgis.org>`_).

#. In QGIS, open ``Plugins > Manage and Install Plugins...``.
#. Search for ``OpenNHMQGisConnector`` in the ``All`` tab and click ``Install Plugin``.
#. Make sure the plugin is enabled in the ``Installed`` tab.

Install the DebrisFrame package
""""""""""""""""""""""""""""""""""""""""

#. Open the Processing Toolbox (``Processing > Toolbox``).
#. Expand ``OpenNHM > Admin`` and run ``Install DebrisFrame``.

The tool installs the ``debrisframe`` package from PyPI. DebrisFrame requires
AvaFrame ``>= 2.2``. If an older AvaFrame is already installed, you are asked
before it is replaced.

If you prefer to install AvaFrame yourself, or if the installation via the
tool fails, run::

  python -m pip install --user --upgrade avaframe

On Windows, open the **OSGeo4W Shell** from the start menu and run the command there.
If you have multiple QGIS versions installed, choose the OSGeo4W Shell that matches
your QGIS version.

Restart QGIS afterwards for the DebrisFrame tools to appear.

Run a module
""""""""""""

After restarting QGIS, the DebrisFrame tools appear in the Processing Toolbox
under ``DebrisFrame_Experimental``. See :doc:`connector` for an overview of the
available tools and :ref:`workflow:Application via QGIS` for how to run them.


