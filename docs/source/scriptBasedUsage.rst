Script-based usage
------------------------

After the `installation of DebrisFrame <https://docs.debrisframe.org/en/latest/installation.html#>`_
make sure you change to your ``DebrisFrame`` directory by::

  cd [YOURDIR]/DebrisFrame/debrisframe/data/[DEBRIS]

Replace ``[YOURDIR]`` and ``[DEBRIS]`` with the directory from your installation step and your
debris-flow directory, respectively.

Make sure you have all the input data you need to run the modules you want to execute (:doc:`moduleC1TIF`, :doc:`moduleIn2DFHyd`).

If desired, you can modify the configuration settings as described in :ref:`moduleC1TIF:Model configuration`.

Then run ::

  [YOURDIR]/DebrisFrame/debrisframe/ pixi run python runC1TIF.py