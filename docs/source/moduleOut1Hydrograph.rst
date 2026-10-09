out1Hydrograph: Output Hydrograph Module
=======================================

:py:mod:`out1Hydrograph` is a module for extracting discharge hydrographs at user-defined
cross sections from debris-flow simulations performed with :py:mod:`c1TIF`.

During the simulation, the discharge through each cross section is calculated
from the simulated flow thickness and velocity fields. The results are saved as
time-dependent discharge tables and plotted together with the cumulative flow volume.
Several output cross sections can be evaluated in one simulation.

.. Note::
   The module is still under development and all functions are not fully tested yet!

Theory
------

1. Output cross sections
^^^^^^^^^^^^^^^^^^^^^^^^

The output cross sections are defined by line geometries in a shapefile.
Each line is identified by a unique ``station`` attribute and represented by a
starting and an ending point. The lines are mapped to the DEM raster grid using
:py:func:`in2TopoHyd.getCrossSectionCells`, which identifies the raster cells
along each cross section and returns their row and column indices.

For each cross section, the module calculates a horizontal unit normal vector
perpendicular to the direction from its first to its last raster cell:

.. math::

   \mathbf{n} = (n_x,n_y)
   = \frac{1}{\sqrt{\Delta x^2+\Delta y^2}}
     (-\Delta y,\Delta x).

The normal vector is used to project the simulated velocity onto the flow
direction through the cross section.

2. Cross-section cell widths
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The centers of the selected raster cells are projected orthogonally onto the
straight cross-section line. The projection is restricted to that segment.
The distances between consecutive projected centers are then used to assign
an effective width :math:`\Delta s_i` to each cross-section cell.
Interior cells receive half of the distance to each neighbor, whereas
the first and last cells receive half of their distance to the
adjacent projected center.

This approach accounts for output cross sections that are not aligned with the
DEM raster axes.

3. Flow depth and discharge
^^^^^^^^^^^^^^^^^^^^^^^^^^^

For every evaluated simulation timestep, the flow thickness ``FT`` and horizontal
velocity components ``Vx`` and ``Vy`` are read from the :py:mod:`com1DFA` fields
at the selected raster cells.

Because ``FT`` is the thickness measured normal to the terrain, it is converted
to the vertical flow depth :math:`h_i` using the vertical component
:math:`n_{z,i}^{\mathrm{DEM}}` of the normalized terrain normal:

.. math::

   h_i = \frac{FT_i}{n_{z,i}}.

The volumetric discharge :math:`Q` [m³/s] through an output cross section is
calculated by summing the contributions of all its cells:

.. math::

   Q(t) = \sum_i
   \left(v_{x,i}(t)\,n_{x,i} + v_{y,i}(t)\,n_{y,i}\right)
   h_i(t)\,\Delta s_i.

Here :math:`v_x` and :math:`v_y` are the horizontal velocity components [m/s],
:math:`h` is the vertical flow depth [m], and :math:`\Delta s` is the effective
cross-section cell width [m].

4. Cumulative volume
^^^^^^^^^^^^^^^^^^^^

The discharge is stored as a time series for every output cross section.
For plotting, the cumulative flow volume :math:`V` [m³] is computed by
trapezoidal integration:

.. math::

   V_k = \sum_{j=0}^{k-1}
   \frac{Q_j + Q_{j+1}}{2}\,\Delta t.

Input
-----

The :py:mod:`out1Hydrograph` module requires:

* A **DEM**, used to assign raster cells to the output cross sections and
  determine the terrain-normal components.
* **Output cross sections**, provided as a shapefile in ``Inputs/OUTHYDR``.

The files are organized within a DebrisFrame process directory:

.. code-block:: text

   NameOfDebrisFlow/
     Inputs/
       DEM raster file
       OUTHYDR/
         outputHydrograph.shp       # output cross-section lines
         outputCrossSection.csv     # automatically generated before simulation
     Outputs/
       out1Hydrograph/
         outputCoordinates.csv      # coordinates of cross-section cell centers and projected cell centers
                                    # for plausability checks
         outputHydrographDF_<simHash>.csv      # output hydrograph
         Plots/
           outputHydrograph_<simHash>_XS <station>.png      # plotted hydrograph and cumulative volume

Output cross sections
^^^^^^^^^^^^^^^^^^^^^

The module reads an output-hydrograph shapefile from ``Inputs/OUTHYDR``.
Each cross-section geometry must be represented by two endpoints, and the
attribute field ``station`` must exist, contain no missing values and have
unique identifiers. Multiple output cross sections can be included in one
shapefile.

.. Note::
   The cross sections should be placed approximately perpendicular to the
   expected flow direction. Their endpoints must be different, and the lines
   should lie within the DEM domain.

Model configuration
^^^^^^^^^^^^^^^^^^^

The output hydrograph calculation is enabled in the :py:mod:`c1TIF`
configuration file, ``c1TIF/c1TIFCfg.ini`` (or its local override):

.. code-block:: ini

   [com1DFA_com1DFA_override]
   outputHydrograph = True

When enabled, ``runC1TIF.py`` automatically calls
``out1Hydrograph.out1HydrographMain`` before starting the simulation.

Output
------

Cross-section data for com1DFA
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before the simulation, ``Inputs/OUTHYDR/outputCrossSection.csv`` is automatically generated.
It contains one row per intersected raster cell, with the columns:

* ``station`` — identifier of the output cross section;
* ``row`` and ``column`` — raster indices of the cell;
* ``Nx`` and ``Ny`` — components of the horizontal cross-section normal;
* ``distance`` — effective cell width along the cross section [m].

Cross-section coordinates
^^^^^^^^^^^^^^^^^^^^^^^^^

``Outputs/out1Hydrograph/outputCoordinates.csv`` contains the columns
``station``, ``x``, ``y``, ``projCtreX`` and ``projCtreY``.
These are the cell-center coordinates and their projections onto the
associated output line. The file can be used to check the placement and
rasterization of the output cross sections.

Discharge hydrographs
^^^^^^^^^^^^^^^^^^^^^

After the simulation, the file
``Outputs/out1Hydrograph/outputHydrographDF_<simHash>.csv`` contains the
simulated discharge hydrographs. The index column is ``timestep`` [s],
followed by one column per cross section, named ``XS <station>``.
Each value represents the calculated discharge [m³/s] through that cross
section at the corresponding recorded simulation time.

Plots
^^^^^

For every output cross section, the module creates a figure in
``Outputs/out1Hydrograph/Plots``. The figure shows the discharge hydrograph
[m³/s] and the estimated cumulative flow volume [m³] as functions of time.
The filenames contain the simulation hash and the cross-section identifier.

To run
------

* Go to ``DebrisFrame/debrisframe``.
* Create a process directory containing the required DEM and an output
  cross-section shapefile in ``Inputs/OUTHYDR``.
* Copy ``debrisframeCfg.ini`` to ``local_debrisframeCfg.ini`` and set the
  desired process directory under ``[MAIN] avalancheDir``.
* Copy ``c1TIF/c1TIFCfg.ini`` to ``c1TIF/local_c1TIFCfg.ini`` and set
  ``outputHydrograph = True`` in the ``[com1DFA_com1DFA_override]`` section.
* Run the :py:mod:`c1TIF` simulation:

  .. code-block:: console

     pixi run python runC1TIF.py

The script prepares the output-cross-section cells, runs the
:py:mod:`com1DFA` computation and writes the discharge hydrographs and plots.
The module works for any kind of starting condition (release area, hydrograph).

To generate only the cross-section files, without running the simulation,
execute:

.. code-block:: console

   pixi run python runOut1Hydrograph.py

This standalone script also requires ``outputHydrograph = True`` in the
:py:mod:`c1TIF` configuration. It produces ``outputCrossSection.csv`` and
``outputCoordinates.csv`` but does not compute discharge hydrographs.
This run script's elementary purpose is for debugging reasons.