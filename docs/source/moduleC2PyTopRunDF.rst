c2PyTopRunDF: semi-empirical simulation tool
=======================================

The c2ToprunDF module executes the `pyTopRunDF <https://github.com/schidli/pyTopRunDF#>`_ tool,
its documentation can be find `here <https://github.com/schidli/pyTopRunDF#>`_.
To run c2TopRunDF, clone the current pyTopRunDF version first::

  cd [YOURDIR]/DebrisFrame/debrisframe
  git submodule update --init
  cp debrisframeCfg.ini local_debrisframeCfg.ini

and edit ``local_debrisframeCfg.ini`` with your favorite text editor and adjust the variable
``avalancheDir`` for example to ``data/debrisTopRun``, then run::

  python runC2TopRunDF.py


The input parameters are defined in ``c2TopRunDF/c2TopRunDFCfg.ini``. To change them first copy the file::

  cp c2TopRunDF/c2TopRunDFCfg.ini c2TopRunDF/local_c2TopRunDFCfg.ini

and change the parameters in ``c2TopRunDF/local_c2TopRunDFCfg.ini``.


In comparison to `pyTopRunDF <https://github.com/schidli/pyTopRunDF#>`_:

* **DEM**: the input DEM (as ``*.asc`` file) is in ``avalancheDir/Inputs``
  (the ``avalancheDir`` is defined in ``local_debrisframeCfg.ini``).
* **Release point**: the release point (starting point of the simulation) can be provided

  * as coordinates ``xKoord`` and ``yKoord`` in ``c2TopRunDF/local_c2TopRunDFCfg.ini``, or
  * as a shapefile (``*.shp``) in ``avalancheDir/Inputs/REL``, if ``xKoord`` or ``yKoord`` are left empty.
    The shapefile must contain exactly one point, and only one shapefile is allowed in this folder.

  The coordinates have to lie within the DEM and must be given in the same projection as the DEM.
  If coordinates are given in the configuration file, they are used and the shapefile is ignored.
* **Outputs**: the results are saved in ``avalancheDir/Outputs/c2TopRunDF``:

  * ``depo.asc``: deposition heights as raster file (same extent and cell size as the DEM)
  * ``<name>_deposition.png``: plot of the deposition heights on a hillshade of the DEM, where ``<name>`` is the
    scenario name defined in the configuration file

* **One scenario**: up to now, only one scenario can be computed per run.

