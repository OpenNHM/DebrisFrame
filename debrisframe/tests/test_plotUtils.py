"""
Pytest for module in1Utils.plotUtils
"""

import numpy as np

from debrisframe.in1Utils import plotUtils


def test_plotRatingCurve_createsPlotsDirectory(tmp_path):
    """Check that a standalone call creates the Plots directory it writes into."""
    ratingCurve = {
        "thickness": np.array([0.5, 1.0]),
        "flowArea": np.array([1.0, 4.0]),
        "surfElev": np.array([3.5, 4.0]),
        "xmin": [[0.0], [0.0, 2.0]],
        "xmax": [[2.0], [2.0, 4.0]],
    }
    crossSection = {
        "s": np.array([0.0, 2.0, 4.0]),
        "elevation": np.array([5.0, 3.0, 5.0]),
        "sLevee": np.array([0.0, 4.0]),
        "elevLevee": np.array([5.0, 5.0]),
    }

    plotUtils.plotRatingCurve(ratingCurve, crossSection, tmp_path)

    assert (tmp_path / "Plots" / "ratingCurve.png").is_file()
