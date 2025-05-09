# DebrisFrame

Install DebrisFrame (Linux)
------------------------------

Running DebrisFrame means running AvaFrame's com1DFA with parameters for debris flow:

Install [git](https://github.com/git-guides/install-git), python and [pixi](https://pixi.sh/latest/#installation).

Clone the DebrisFrame repository (in a directory of your choice: [YOURDIR]) and change into it:

```
  cd [YOURDIR]
  git clone https://github.com/OpenNHM/DebrisFrame.git
  cd DebrisFrame
```

Run pixi:

```
pixi shell
```

Try a first run:

change into your ``debrisframe`` directory (replace [YOURDIR] with your path from the installation steps):

```
  cd [YOURDIR]/DebrisFrame/debrisframe
  python runComo1Debris.py
```
