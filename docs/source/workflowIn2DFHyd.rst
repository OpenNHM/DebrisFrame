Workflow: in2DFHyd
===================================

This guide describes how to prepare input data and use :py:mod:`in2DFHyd` to
calculate hydraulic initial conditions for a debris-flow simulation with
:py:mod:`c1TIF`.

**Choose your workflow before running the module:**

* **Script-based usage:** Run ``in2DFHyd`` separately, or let ``runC1TIF.py``
  trigger hydraulic preprocessing automatically (``inputHydrograph = True``).
  Follow :ref:`in2dfhyd-script-workflow`.
* **QGIS usage:** Run ``Hydrograph Starting Condition (in2DFHyd)`` first
  and then ``Thickness integrated flow (c1)`` as two separate QGIS operations.
  Provide the generated CSV file to ``c1``
  manually and keep ``inputHydrograph = False``. Follow
  :ref:`in2dfhyd-qgis-workflow`.

The input data requirements in :ref:`in2dfhyd-inputs` and the output checks in
:ref:`in2dfhyd-outputs` apply to **both** workflows. The folder structure
described in :ref:`in2dfhyd-inputs` is only required for script-based usage.
QGIS users can load or create the input data directly in their QGIS project.

For details about the underlying methods and configuration parameters, see
:doc:`moduleIn2DFHyd`.

.. note::

   The ``in2DFHyd`` module is still under development. The recommendations
   below reflect the workflow described for the current development stage;
   not all functions have been fully tested.

.. _in2dfhyd-inputs:

1. Prepare the input data
-------------------------

**Script-based usage:** Create a debris-flow process directory with the
following structure::

   NameOfDebrisFlow/
     Inputs/
       <DEMname>.asc or <DEMname>.tif
       HYDR/
         <hydrographName>.csv
       LEVEE/
         <leveePointsName>.shp
       XSECT/
         <crossSectionLineName>.shp

The ``HYDR``, ``LEVEE`` and ``XSECT`` directories contain the discharge
hydrograph, the levee points and the cross section line, respectively.

**QGIS usage:** This separate folder structure is **not required**.
Load the DEM and hydrograph directly into the QGIS workflow, and load or
create the cross section line and levee-point layers in your QGIS project.
Select the corresponding inputs in the ``Hydrograph Starting Condition (in2DFHyd)`` tool interface.
The same input data requirements described below still apply.

The module settings are defined in ``in2DFHydCfg.ini``, or in ``c1TIFCfg.ini``
when hydraulic preprocessing is started through ``c1TIF``. The execution
options are described separately in Sections 2 and 3 below. For all module
parameters, see :doc:`moduleIn2DFHyd`.

1.1 Digital elevation model (DEM)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For script-based usage, place the DEM raster in the ``Inputs`` directory;
for QGIS, load the DEM as a raster layer and select it in the tool.
The module supports different raster resolutions. The ``meshCellSize`` parameter controls the
cell size used for processing (2 m by default in the documented ``c1TIF``
configuration). It is recommended to use the same cell size for hydraulic
preprocessing and the subsequent simulation. If the input DEM has a different
cell size, it is remeshed to the configured ``meshCellSize``. See the
`AvaFrame DEM input documentation <https://docs.avaframe.org/en/latest/moduleCom1DFA.html#dem-input-data>`_.

1.2 Hydrograph
~~~~~~~~~~~~~~

For script-based usage, save the hydrograph as
``Inputs/HYDR/<hydrographName>.csv``. For QGIS, select the hydrograph CSV
directly in the tool interface. The CSV file must
contain exactly two comma-separated columns: ``timestep`` and ``discharge``.

The required units are:

* ``timestep``: time in seconds [s].
* ``discharge``: debris-flow discharge in cubic metres per second [m³/s].

For testing, a time interval of 1 s is recommended. If the module reports
that particles from the previous timestep have not yet left the release
cells, potentially causing numerical instability, increase the hydrograph
time interval.

1.3 Cross section line
~~~~~~~~~~~~~~~~

The cross section line defines the terrain cross section at which the hydrograph
is applied as a boundary condition.

In QGIS, create a **line shapefile** layer. For script-based usage, save it
as ``Inputs/XSECT/<crossSectionLineName>.shp``; for the QGIS usage,
use the layer directly in the tool interface. Use the same coordinate reference
system (CRS) as the DEM. Draw the line across the channel, perpendicular to
the expected flow direction. The line must have **exactly two vertices**: a
starting point and an ending point.

.. figure:: _static/crossSectionLine.png
    :width: 90%

    Cross section line (red) and corresponding starting and ending points

.. important::

   Choosing an appropriate cross section line is the user's responsibility.
   The line must be perpendicular to the flow direction; otherwise,
   plausible simulation results cannot be guaranteed.

1.4 Levee points
~~~~~~~~~~~~~~~~

The two levee points define the lateral extent of the channel. They exclude
low-lying floodplain areas outside the channel from the initial condition.
The discharge prescribed by the hydrograph is initialized only between these
points.

Create a **point shapefile** layer in QGIS. For script-based usage, save it
as ``Inputs/LEVEE/<leveePointsName>.shp``; for the QGIS usage, use
the layer directly in the tool interface.
Use the same CRS as the DEM and the cross section line. The shapefile must contain
**exactly two points**, one on each side of the channel.

.. figure:: _static/leveePoints.png
    :width: 90%

    Cross section and corresponding levee points (red)

To select suitable locations, use the QGIS terrain-profile plugin
``Profile tool``:

#. Draw a profile along the previously defined cross section line.
#. Inspect the DEM elevation profile in the plugin window.
#. Enable the option to display the cursor position.
#. Move the cursor to the desired levee location in the profile. The
   corresponding position is also shown in the main QGIS map window.
#. Place the two levee points at the selected locations.

.. figure:: _static/profileTool.png
    :width: 90%

    Determination of levee-point positions using ``Profile tool``

The levee points are assigned to the closest cross-section points.

The module checks whether the channel can accommodate the specified discharge
at each timestep. In the documented implementation, it stops with an error
if the discharge exceeds the channel's capacity. Overtopping at the cross
section line is not yet supported.

.. _in2dfhyd-script-workflow:

2. Script-based usage
---------------------

Use this section when starting DebrisFrame from Python scripts, **not** from
the QGIS connector. There are two options:

**Option A — Run hydraulic preprocessing separately**

#. First change the directory to ``DebrisFrame/debrisframe``
#. Prepare the input files as described in Section 1.
#. Copy ``in2DFHyd/in2DFHydCfg.ini`` to ``in2DFHyd/local_in2DFHydCfg.ini`` and, if desired, change the configuration settings (optional).
#. To generate the hydraulic initial conditions.run:
    ::

     pixi run python runIn2DFHyd.py

   See also :doc:`scriptBasedUsage`.
#. Check the generated files as described in Section 4.
#. When subsequently running ``c1TIF`` separately, ensure that the generated
   initial-condition CSV is provided as its time-dependent release input
   (or placed in ``Inputs/REL`` where required by the chosen execution).

**Option B — Start hydraulic preprocessing automatically from c1TIF**

#. Change the directory and prepare the same input files as described in Section 1.
#. Copy ``in2DFHyd/in2DFHydCfg.ini`` to ``in2DFHyd/local_in2DFHydCfg.ini`` and set ``inputHydrograph = True`` in ``c1TIFCfg.ini``.
#. Execute ``runC1TIF.py``. The ``c1TIF`` workflow starts ``in2DFHyd``
   preprocessing before the simulation; see
   :ref:`moduleC1TIF:Run from hydrograph` and :doc:`scriptBasedUsage`.
#. Check the generated hydraulic outputs and the simulation results.

.. important::

   ``inputHydrograph = True`` is the setting for **script-based, integrated**
   preprocessing (Option B). It is **not** the recommended setting for the
   QGIS workflow described in Section 3.

.. _in2dfhyd-qgis-workflow:

3. QGIS usage
-------------------

Use this section when running the modules through the **QGIS connector**.
Unlike script-based Option B, the hydraulic preprocessing and simulation
must be started **separately and in this order** in the documented version.
See :doc:`connector` for general connector instructions.

#. Prepare the DEM, hydrograph, cross section line and levee points as in
   Section 1.
#. Run the **Hydrograph Starting Condition (in2DFHyd)** tool in QGIS to generate the hydraulic initial
   conditions.
#. Check the ``in2DFHyd`` output CSV and plots (Section 4).
#. Open the **c1** tool in QGIS. Select
   ``Outputs/in2DFHyd/<crossSectionName>.csv`` as the
   *Time dependent release values / release geometry* input.
#. Keep ``inputHydrograph = False`` in ``c1TIFCfg.ini`` and run ``c1TIF``.

.. warning::

   Do not use ``inputHydrograph = True`` to trigger preprocessing when running
   ``c1TIF`` via the QGIS connector. In the documented development version,
   this may cause an error. Instead, execute ``in2DFHyd`` first and pass its
   CSV output explicitly to ``c1TIF`` as described above.

.. _in2dfhyd-outputs:

4. Check the output data
------------------------

The ``in2DFHyd`` outputs are organized as follows::

   NameOfDebrisFlow/
     Outputs/
       in2DFHyd/
         <crossSectionName>.csv                         (named after the XSECT shapefile)
         <crossSectionName>_crossSectionCells.csv       (optional)
         Plots/
           <crossSectionName>_crossSection.png
           <crossSectionName>_ratingCurve.png

For more details, see :ref:`moduleIn2DFHyd:Output`.

``<crossSectionName>.csv``
   Contains the spatially distributed hydraulic initial conditions used by
   ``c1TIF``. In the integrated script workflow, they may be transferred
   automatically; in the QGIS workflow, you must select this file explicitly.
   For a separate script-based simulation, ensure it is available as the
   required release input.

``<crossSectionName>_crossSectionCells.csv``
   Contains coordinates and elevations of cell centres mapped along the cross
   section line. It is written if ``exportCrossSectionCells = True``. Load
   these coordinates into QGIS to verify the representation on the model grid.

``<crossSectionName>_crossSection.png``
   Shows the terrain cross section and the levee-point positions. Verify that
   the channel geometry and lateral boundaries are plausible.

``<crossSectionName>_ratingCurve.png``
   Shows the cross-sectional geometry and the relationship between flow area
   and flow thickness. Use it to check the hydraulic plausibility of the
   derived initial conditions.

5. Troubleshooting checklist
----------------------------

If preprocessing or the subsequent simulation fails, check the following:

* **Script-based usage:** Are the project directory and the ``Inputs/HYDR``, ``Inputs/LEVEE`` and
  ``Inputs/XSECT`` subdirectories named correctly?
* **QGIS usage:** Are all required input files or layers loaded or
  created in the QGIS project and selected in the tool interface?
* Do the DEM, cross section line and levee points use the same CRS?
* Does the cross section line contain exactly two vertices and run across the
  channel, perpendicular to the expected flow direction?
* Does the levee-point shapefile contain exactly two points, correctly
  positioned away from the cross section endpoints?
* Do the hydrograph columns, units and timestep interval match the required
  format?
* Are the output plots plausible? They may explain error messages.
* **Script-based integrated preprocessing:** Is ``inputHydrograph = True``
  set in ``c1TIFCfg.ini``?
* **QGIS usage:** Was ``in2DFHyd`` run first, is
  ``inputHydrograph = False``, and was the generated CSV explicitly selected
  as the time-dependent release input for ``c1TIF``?
* **Separate script-based runs:** Is the generated initial-condition CSV
  available to ``c1TIF`` (for example in ``Inputs/REL`` where applicable)?
* If errors involving the cross section line or levee points persist, try
  deleting and redrawing them in QGIS.
* Does the hydrograph discharge remain within the channel capacity?
  Overtopping at the cross section line is not supported in the documented
  implementation.
