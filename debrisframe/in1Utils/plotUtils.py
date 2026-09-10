"""
Plotting helper functions
"""

# load modules
import matplotlib.pyplot as plt

# local imports
import avaframe.in3Utils.fileHandlerUtils as fU


def plotCrossSection(crossSection, outputDir):
    """
    This function plots the terrain cross section

    Parameters
    -----------
    crossSection: dict
        dictionary containing
        the elevation of the cross-section cells and levee points,
        the path along (distance) along the cross-section cells
    outputDir: str or Path
        path to output directory of in2TopoHyd module

    Returns
    --------
    Plot: .png
        saves plot in debris-flow directory
    """

    # plot cross section
    fig, ax = plt.subplots(figsize=(10, 8))

    ax.plot(crossSection["s"], crossSection["elevation"])
    ax.scatter(crossSection["sLevee"], crossSection["elevLevee"], color="red", label="Levee points")
    ax.set_xlabel("distance [m]")
    ax.set_ylabel("elevation [m]")
    ax.grid(color="gray", linestyle="--", linewidth=0.5, alpha=0.6)
    ax.set_title("Cross Section")

    plt.legend()
    plt.tight_layout()

    # check if directory already exists
    path = outputDir / "Plots"
    fU.makeADir(path)

    fig.savefig(path / "crossSection.png")


def plotRatingCurve(ratingCurve, crossSection, outputDir):
    """
    This function plots the terrain cross section
    and the corresponding rating curve

    Parameters
    -----------
    ratingCurve: dict
        dictionary containing
        thickness values/surface elevations and corresponding flow area
        min and max values of horizontal distance of flow area
    crossSection: dict
            dictionary containing
            the elevation of the cross-section cells,
            the path along (distance) along the cross-section cells
    outDir: str or Path
            path to output directory of in2TopoHyd module

    Returns
    --------
    Plot: .png
        saves plot in debris-flow directory
    """

    thickness = ratingCurve["thickness"]
    flowArea = ratingCurve["flowArea"]
    surfElev = ratingCurve["surfElev"]
    xmin = ratingCurve["xmin"]
    xmax = ratingCurve["xmax"]

    # plot cross section
    fig, ax = plt.subplots(ncols=1, nrows=2, figsize=(10, 8))

    ax[0].plot(crossSection["s"], crossSection["elevation"])
    ax[0].scatter(crossSection["sLevee"], crossSection["elevLevee"], color="red", label="Levee points")
    ax[0].hlines(
        surfElev, xmin=xmin, xmax=xmax, linestyles="--", colors="grey", lw=0.5, label="elevation increments"
    )
    ax[0].set_xlabel("distance [m]"), ax[0].set_ylabel("elevation [m]")
    ax[0].grid(color="gray", linestyle="--", linewidth=0.5, alpha=0.6)
    ax[0].set_title("Cross Section")
    ax[0].legend()

    ax[1].plot(thickness, flowArea)
    ax[1].set_xlabel("flow thickness [m]")
    ax[1].set_ylabel("flow area [m²]")
    ax[1].grid(color="gray", linestyle="--", linewidth=0.5, alpha=0.6)
    ax[1].set_title("Rating Curve")

    plt.tight_layout()

    path = outputDir / "Plots" / "ratingCurve.png"
    fig.savefig(path)
