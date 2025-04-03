Install DebrisFrame (Linux)
------------------------------
  
Running DebrisFrame means running AvaFrame's com1DFA with parameters for debris flow:

Create a new `conda environment <https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html>`_ for DebrisFrame, activate it and install pip, numpy and cython in this environment::


  conda create --name debrisframe_env
  conda activate debrisframe_env
  conda install pip numpy cython


Clone the DebrisFrame repository (in a directory of your choice: [YOURDIR]) and change into it::


  cd [YOURDIR]
  git clone https://github.com/OpenNHM/DebrisFrame.git
  cd DebrisFrame


Install debrisframe and its requirements by either doing::


  pip install -e .


Try a first run:

change into your ``debrisframe`` directory (replace [YOURDIR] with your path from the installation steps)::


  cd [YOURDIR]/DebrisFrame/debrisframe
  python runComo1Debris.py


  

