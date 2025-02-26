# DebrisFrame

Install DebrisFrame
------------------------------

Running DebrisFrame means running AvaFrame's com1DFA with parameters for debris flow:

Install AvaFrame as described in the [Avaframe documentation](https://docs.avaframe.org/en/latest/developinstall.html#advanced-installation-linux)

Clone the DebrisFrame repository (into the same directory, where the Avaframe folder is cloned into: [YOURDIR]) and change into it:

  cd [YOURDIR]
  git clone https://github.com/OpenNHM/DebrisFrame.git
  cd DebrisFrame

- try a first run:

change into your ``debrisframe`` directory (replace [YOURDIR] with your path from the installation steps)::

  cd [YOURDIR]/DebrisFrame/debrisframe
  python runComo1Debris.py