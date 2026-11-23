OpenNHM QGis Connector
======================

The OpenNHM QGis Connector allows QGis users to run DebrisFrame modules directly from QGis. The connector only
provides the interface to functions within the DebrisFrame (and AvaFrame) python package, and is developed separately,
see the `OpenNHMQGisConnector github repository <https://github.com/OpenNHM/OpenNHMQGisConnector>`_.
It makes use of the QGis processing plugin, which is included in all current QGis releases.
For the installation, see :ref:`installationFromQGis`.

.. Note::
   The DebrisFrame tools only show up in the Processing Toolbox if the ``debrisframe`` python package is actually
   installed in QGis's Python environment. Use the ``Install DebrisFrame`` tool (see `Admin`_) to install it.

.. Note::
   ALL (!!) data provided to the functions below HAVE to be in the same projection. It does not matter which
   projection is used as long as it is the same one.

Experimental
------------

The DebrisFrame tools are found in the Processing Toolbox under ``DebrisFrame_Experimental``.
Each tool corresponds to a DebrisFrame module and exposes its inputs and outputs as QGis processing parameters.
For details on the underlying modules, see the linked module pages.

.. glossary::
   :sorted:

   Thickness integrated flow (c1)
      Runs a thickness integrated debris flow simulation via module :py:mod:`c1TIF`.

      Inputs:

      * ``DEM layer`` (required) - raster layer.
      * ``Release layer(s)`` (optional) - required only if the csv file has no x/y columns.
      * ``Time dependent release values / release geometry`` (optional) - csv file; defines the release
        geometry if it contains x/y columns. The ``<crossSectionName>.csv`` (named after the ``XSECT`` shapefile)
        produced by the *Hydrograph Starting Condition (in2TopoHyd)* tool can be used here as the time dependent
        release input.
      * ``Secondary release layer`` (optional) - only one is allowed.
      * ``Entrainment layer`` (optional) - only one is allowed.
      * ``Resistance layer`` (optional) - only one is allowed.
      * ``Destination folder`` (required) - process directory.
      * ``Expert configuration file`` (advanced, optional) - ``c1TIFCfg.ini``. See
        :ref:`moduleC1TIF:Model configuration`.

      Outputs:

      * ``Output layer`` - simulation result.

   Hydrograph Starting Condition (in2TopoHyd)
      Computes the initial conditions at a release line via module :py:mod:`in2TopoHyd`.
      The resulting ``<crossSectionName>.csv`` (named after the ``XSECT`` shapefile) can be used as the time
      dependent release input (``Time dependent release values / release geometry``) for the
      *Thickness integrated flow (c1)* tool.

      Inputs:

      * ``DEM layer`` (required) - raster layer.
      * ``Release line`` (required) - line with exactly two points (start and end).
      * ``Levee points`` (required) - two points, left and right bank.
      * ``Hydrograph csv file`` (required) - csv file with the columns ``timestep`` (values in [s]) and
        ``discharge`` (values in [m³/s]).
      * ``Destination folder`` (required) - process directory.
      * ``Expert configuration file`` (advanced, optional) - ``in2TopoHydCfg.ini``. See
        :ref:`moduleIn2TopoHyd:Model configuration`.

      Outputs:

      * ``Cross section cells`` - point layer.

   pyTopRunDF (c2)
      Runs the semi-empirical simulation tool pyTopRunDF via module c2TopRunDF. For more info see
      :doc:`moduleC2PyTopRunDF`.

      Inputs:

      * ``DEM layer`` (required) - raster layer.
      * ``Release point`` (required) - exactly one point. It is transformed to the projection of the DEM if
        necessary.
      * ``Destination folder`` (required) - process directory.

      Outputs:

      * ``Output layer`` - deposition thickness raster layer(s).

   Get default DebrisFrame module ini
      Extracts the default configuration ini file for the selected DebrisFrame module. The file can then be
      edited and supplied as the expert configuration file when running the corresponding simulation tool.

      Inputs:

      * ``Module`` (required) - select either ``c1TIF`` or ``in2TopoHyd``.
      * ``Destination file`` (required) - ini file to write.

      Outputs:

      * the written ini file.


Admin
-----

.. glossary::
   :sorted:

   Install DebrisFrame
      Installs the ``debrisframe`` package from PyPI. DebrisFrame requires AvaFrame ``>= 2.2``. If an older AvaFrame
      is already installed, you are asked before it is replaced. The input is purely a dummy input, needed for the
      tool window to show up. Restart QGis afterwards for the DebrisFrame tools to appear.

   GetVersion
      Displays the current version of the AvaFrame python package (NOT the OpenNHM QGis Connector).

   UpdateAvaFrame
      Updates the AvaFrame python package.
