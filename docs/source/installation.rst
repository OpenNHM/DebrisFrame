Install DebrisFrame
---------------------
  
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


  

