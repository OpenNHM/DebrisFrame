"""
Pytest for module out1Hydrograph
"""

import numpy as np
import pytest

from debrisframe.out1Hydrograph import out1Hydrograph

def test_projectCellCenterToLine():
    """correct projection of cross-section cell centers"""

    #++ vertical cross-section line
    csz = 1.0
    length = 10
    crossSectionLine = {"x": np.array([1.0, 1.0]), "y": np.array([0.0, length])}
    # shift cross-section cells -1 in x-direction
    crossSectionCells = {"x": np.zeros(length), "y": np.arange(0.5, 10.5, csz)}
    expectedS = np.ones(length - 2)
    expectedS = np.concatenate(([0.5], expectedS, [0.5]))
    expectedX = np.ones(length)
    expectedY = np.arange(0.5, 10.5, csz)
    

    projX, projY, projS = out1Hydrograph.projectCellCenterToLine(crossSectionLine, crossSectionCells)

    np.testing.assert_allclose(projX, expectedX)
    np.testing.assert_allclose(projY, expectedY)
    np.testing.assert_allclose(projS, expectedS)

    #++ horizontal cross-section line
    crossSectionLine = {"x": np.array([0.0, length]), "y": np.array([1.0, 1.0])}
    # shift cross-section cells -1 in y-direction
    crossSectionCells = {"x": np.arange(0.5, 10.5, csz), "y": np.zeros(length)}
    expectedS = np.ones(length - 2)
    expectedS = np.concatenate(([0.5], expectedS, [0.5]))
    expectedX = np.arange(0.5, 10.5, csz)
    expectedY = np.ones(length)

    projX, projY, projS = out1Hydrograph.projectCellCenterToLine(crossSectionLine, crossSectionCells)
    
    np.testing.assert_allclose(projX, expectedX)
    np.testing.assert_allclose(projY, expectedY)
    np.testing.assert_allclose(projS, expectedS)

    #++ diagonal cross-section line
    dx = 9.0
    dy = 10.0
    crossSectionLine = {"x": np.array([0.0, dx]), "y": np.array([0.0, dy])}
    # shift cross-section cells +1 in x-direction
    crossSectionCells = {"x": np.arange(1.0, 11.0, 1), "y": np.arange(0.0, 10.0, 1)}

    ## compute expected values
    def funX(dx, dy, y):
        return dx / dy * y
    # distance between cross-section cell and projected point
    yLine = np.arange(0., 10., 1)
    xLine = funX(dx, dy, yLine)
    dLC = crossSectionCells["x"] - xLine
    # scalar product of dLC and direction vector of cross-section line
    scalarProd = dx * dLC + dy * 0
    # get distance l between projected point and point on line on same height as cross-section cell
    mag = np.sqrt((dx**2 + dy**2) * (dLC**2))
    cosAngle = scalarProd / mag
    length = dLC * cosAngle
    # unit vector
    mag = np.sqrt(dx**2 + dy**2)
    ex = dx / mag
    ey = dy / mag
    # projected coordinates
    dLx = ex * length
    dLy = ey * length
    expectedX = xLine + dLx
    expectedY = yLine + dLy
    # get distance between projected points
    expectedS = np.hypot(np.diff(expectedX[1:]), np.diff(expectedY[1:]))
    expectedS = np.concatenate(([expectedS[0]/2], expectedS, [expectedS[-1]/2]))
    
    projX, projY, projS = out1Hydrograph.projectCellCenterToLine(crossSectionLine, crossSectionCells)

    np.testing.assert_allclose(projX, expectedX)
    np.testing.assert_allclose(projY, expectedY)
    np.testing.assert_allclose(projS, expectedS)

    #++ Projected points outside the endpoints are clamped to the segment
    line = {"x": np.array([0.0, 4.0]), "y": np.array([0.0, 0.0])}
    centers = {"x": np.array([-2.0, 2.0, 7.0]), "y": np.array([3.0, -2.0, 5.0])}

    proj_x, proj_y, distance = out1Hydrograph.projectCellCenterToLine(line, centers)

    np.testing.assert_allclose(proj_x, [0.0, 2.0, 4.0])
    np.testing.assert_allclose(proj_y, [0.0, 0.0, 0.0])
    np.testing.assert_allclose(distance, [1.0, 2.0, 1.0])

    #++ Identical line endpoints must raise a meaningful exception
    line = {"x": np.array([1.0, 1.0]), "y": np.array([2.0, 2.0])}
    centers = {"x": np.array([1.0, 2.0]), "y": np.array([2.0, 3.0])}

    with pytest.raises(ValueError, match="starting and ending points must differ"):
        out1Hydrograph.projectCellCenterToLine(line, centers)
