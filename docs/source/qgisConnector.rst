Application via QGIS
---------------------

Install the QGIS connector and DebrisFrame as described in
:ref:`installationFromQGis`. After restarting QGIS, the DebrisFrame tools appear
in the Processing Toolbox under ``DebrisFrame_Experimental``.

Each tool corresponds to a DebrisFrame module and exposes its inputs and outputs
as QGIS processing parameters. Input layers can be loaded or created in the QGIS
project; the ``Inputs/HYDR``, ``Inputs/LEVEE`` and ``Inputs/XSECT`` folder
structure used by the script-based workflow is not required. The tools still
need a destination folder for their generated files.

**For a hydrograph-based c1TIF simulation**, for example, run the tools in this order:

#. Run **Hydrograph Starting Condition (in2DFHyd)** with the DEM, cross section
   line, levee points and hydrograph CSV.
#. Check the generated initial-condition CSV and the hydraulic plots.
#. Run **Thickness integrated flow (c1)** with the DEM and the generated CSV as
   ``Time dependent release values / release geometry``. Keep
   ``inputHydrograph = False`` in the c1TIF configuration for this QGIS route.

For step-by-step instructions see :doc:`workflowIn2DFHyd` and
:doc:`workflowC1TIF`. For module theory and parameters see
:doc:`moduleIn2DFHyd` and :doc:`moduleC1TIF`. For script execution see
:doc:`scriptBasedUsage`.
