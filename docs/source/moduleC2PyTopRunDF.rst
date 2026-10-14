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


In comparison to `pyTopRunDF <https://github.com/schidli/pyTopRunDF#>`_,
the Input DEM (as *.asc file) is in ``avalancheDir/Inputs`` (the ``avalancheDir`` is defined in ``local_debrisframeCfg.ini``).
The input parameters are defined in ``c2TopRunDF/c2TopRunDFCfg.ini``. To change them first copy the file::

  cp c2TopRunDF/c2TopRunDFCfg.ini c2TopRunDF/local_c2TopRunDFCfg.ini

and change the parameters in ``c2TopRunDF/local_c2TopRunDFCfg.ini``.