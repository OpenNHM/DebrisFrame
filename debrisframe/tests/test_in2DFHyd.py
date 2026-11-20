"""
Pytest for module in2DFHyd
"""

import configparser
import warnings

import numpy as np
import pandas as pd
import pytest

from debrisframe.in2DFHyd import in2DFHyd


def _inputHydCfg(dElev="0.5", normalDist="2.0"):
    cfg = configparser.ConfigParser()
    cfg["GENERAL"] = {"dElev": dElev}
    cfg["GENERAL"] = {"normalDist": normalDist}
    return cfg


def _planarDEM(gradient=0.1, cellSize=2.0, nrows=20, ncols=20):
    """Build a synthetic DEM whose elevation increases linearly with x."""
    header = {
        "xllcenter": 0.0,
        "yllcenter": 0.0,
        "cellsize": cellSize,
        "ncols": ncols,
        "nrows": nrows,
    }
    colVals = gradient * (header["xllcenter"] + np.arange(ncols) * cellSize)
    return {
        "header": header,
        "rasterData": np.tile(colVals, (nrows, 1)),
        "areaRaster": np.full((nrows, ncols), cellSize * cellSize),
    }


def _verticalCrossSection(dem, x=10.0, yStart=2.0, yEnd=10.0):
    """Return a cross section along a vertical release line at constant x."""
    releaseLine = {"x": np.array([x, x]), "y": np.array([yStart, yEnd])}
    crossSection = in2DFHyd.getCrossSectionCells(dem, releaseLine)
    crossSection["s"] = np.arange(len(crossSection["x"]), dtype=float) * dem["header"]["cellsize"]
    crossSection["idLevee"] = [1, len(crossSection["x"]) - 2]
    return crossSection


def test_getCrossSectionCells_selects_nearestCellCenter():
    """Check that a release line samples the DEM cell nearest to it.

    A common DEM convention stores cell centers at half-multiples of the cell
    size (xllcenter = xllcorner + cellsize / 2). Snapping the release-line
    coordinates to global multiples of the cell size then shifts the sampled
    cell by one column.
    """
    cellSize = 2.0
    xllcenter = 1001.0
    yllcenter = 2001.0
    dem = {
        "header": {
            "xllcenter": xllcenter,
            "yllcenter": yllcenter,
            "cellsize": cellSize,
        },
        "rasterData": np.zeros((10, 10)),
        "areaRaster": np.full((10, 10), cellSize * cellSize),
    }

    x = 1003.4
    releaseLine = {"x": np.array([x, x]), "y": np.array([2003.0, 2009.0])}

    crossSection = in2DFHyd.getCrossSectionCells(dem, releaseLine)

    # the nearest cell center is at col 1 (x = 1003), not col 2 (x = 1005)
    expectedCol = int(np.round((x - xllcenter) / cellSize))
    assert np.all(crossSection["crossSectIdx"][1] == expectedCol)


def test_getCrossSectionCells_snapsSlantedLineToCellCenters():
    """Check that interpolated cross-section points of a slanted release line

    lie on cell centers, even when the origin is not a multiple of the cell size.
    """
    cellSize = 2.0
    xllcenter = 1001.0
    yllcenter = 2001.0
    dem = {
        "header": {
            "xllcenter": xllcenter,
            "yllcenter": yllcenter,
            "cellsize": cellSize,
        },
        "rasterData": np.zeros((10, 10)),
        "areaRaster": np.full((10, 10), cellSize * cellSize),
    }
    releaseLine = {"x": np.array([1001.0, 1007.0]), "y": np.array([2001.0, 2005.0])}

    crossSection = in2DFHyd.getCrossSectionCells(dem, releaseLine)

    resid = (crossSection["y"] - yllcenter) / cellSize
    assert np.allclose(resid, np.round(resid))
    assert np.all(crossSection["crossSectIdx"][0] == np.round(resid).astype(np.int32))


def test_computeRatingCurve():
    """Check that the function computes the correct rating curve"""

    crossSection = {
        "elevation": np.array([5.0, 5.0, 0.0, 0.0, 0.0, 5.0, 5.0]),
        "s": np.arange(0.0, 7.0, 1.0),
        "idLevee": [1, 5],
        "elevLevee": np.array([5.0, 5.0]),
    }

    ratingCurve = in2DFHyd.computeRatingCurve(crossSection, _inputHydCfg())

    dh = 0.5
    thicknessTest = np.arange(0.5, 5 + dh, dh)
    dHdx = 5.0 / 1.0
    flowAreaTest = thicknessTest * 2.0 + (thicknessTest / dHdx * thicknessTest)
    surfElevTest = thicknessTest + 0.0

    assert np.all(ratingCurve["thickness"] == thicknessTest)
    assert np.all(ratingCurve["flowArea"] == flowAreaTest)
    assert ratingCurve["minElevation"] == 0.0
    assert np.all(ratingCurve["surfElev"] == surfElevTest)
    assert np.all(np.array(ratingCurve["xmin"]) == np.array([[float(2.0 - t / dHdx)] for t in thicknessTest]))
    assert np.all(np.array(ratingCurve["xmax"]) == np.array([[float(4.0 + t / dHdx)] for t in thicknessTest]))


def test_computeRatingCurve_flatChannelRaises():
    """Check that a channel without a levee-to-bottom elevation difference raises explicitly.

    Without the guard, the rating curve comes back empty and the failure only surfaces
    later as a cryptic ``max() arg is an empty sequence`` in computeRelFlowThVel.
    """
    crossSection = {
        "elevation": np.array([10.0, 10.0, 10.0, 10.0, 10.0]),
        "s": np.arange(0.0, 10.0, 2.0),
        "idLevee": [1, 3],
        "elevLevee": np.array([10.0, 10.0]),
    }

    with pytest.raises(ValueError, match="channel"):
        in2DFHyd.computeRatingCurve(crossSection, _inputHydCfg())
    

def test_computeRatingCurve_returnsNonEmptyForValidChannel():
    """Check that a proper V-shaped channel still yields a non-empty rating curve."""
    crossSection = {
        "elevation": np.array([12.0, 11.0, 10.0, 11.0, 12.0]),
        "s": np.arange(0.0, 10.0, 2.0),
        "idLevee": [1, 3],
        "elevLevee": np.array([11.0, 11.0]),
    }

    ratingCurve = in2DFHyd.computeRatingCurve(crossSection, _inputHydCfg())

    assert len(ratingCurve["flowArea"]) > 0
    assert np.all(np.diff(ratingCurve["flowArea"]) > 0)


def test_computeSlopeAlongChannel_planarDEM():
    """Check the central-difference slope recovers the DEM gradient."""
    dem = _planarDEM(gradient=0.1)
    crossSection = _verticalCrossSection(dem)
    cfg = _inputHydCfg()
    cfg["GENERAL"]["normalDist"] = "4"

    slope = in2DFHyd.computeSlopeAlongChannel(dem, crossSection, cfg)

    assert slope == pytest.approx(0.1, abs=1e-6)


def test_getFlowDirection_pointsDownslope():
    """Check the flow direction is a unit vector pointing down the DEM gradient."""
    dem = _planarDEM(gradient=0.1)
    crossSection = _verticalCrossSection(dem)
    cfg = _inputHydCfg()
    cfg["GENERAL"]["normalDist"] = "4"

    flwDir = in2DFHyd.getFlowDirection(crossSection, dem, cfg)

    assert np.linalg.norm(flwDir) == pytest.approx(1.0)
    # downslope is -x for an elevation gradient along +x
    assert flwDir[0] < 0
    assert flwDir[1] == pytest.approx(0.0, abs=1e-6)


def test_assignToWetCell_conservesReleaseVolume():
    """Check the release volume is distributed over the wet cells without losses."""
    cellSize = 2.0
    crossSection = {
        "x": np.array([0.0, 2.0, 4.0, 6.0, 8.0]),
        "y": np.zeros(5),
        "elevation": np.array([5.0, 4.0, 3.0, 4.0, 5.0]),
        "idLevee": [0, 4],
        "actualCellArea": np.full(5, cellSize * cellSize),
    }
    dem = {"header": {"cellsize": cellSize}}
    ratingCurve = {"minElevation": 3.0}
    releaseThickness = np.array([1.5])
    releaseVolume = np.array([6.0])

    wetCells = in2DFHyd.assignToWetCell(crossSection, dem, ratingCurve, releaseThickness, releaseVolume)

    # surface at 4.5 wets the three cells with elevation below 4.5
    assert len(wetCells["wetXcoords"][0]) == 3
    assert np.sum(wetCells["releaseVolume"][0]) == pytest.approx(6.0)


def test_computeRelFlowThVel_unsupportedVelTypeRaises():
    """Check an unsupported velType raises a clear error instead of UnboundLocalError."""
    cfg = _inputHydCfg()
    cfg["GENERAL"]["slope"] = "0.1"
    cfg["GENERAL"]["velType"] = "notAMethod"
    ratingCurve = {"thickness": np.array([0.5, 1.0]), "flowArea": np.array([1.0, 4.0])}
    dem = _planarDEM()
    crossSection = _verticalCrossSection(dem)

    with pytest.raises(ValueError, match="velType"):
        in2DFHyd.computeRelFlowThVel(np.array([1.0, 2.0]), cfg, ratingCurve, dem, crossSection)


def test_assignCrossSectionCoords_picksNearestCell():
    """Check each levee point is mapped to the nearest cross-section cell."""

    # levee points lie within the range of the cross section
    crossSection = {
        "x": np.array([0.0, 2.0, 4.0, 6.0, 8.0]),
        "y": np.zeros(5),
        "elevation": np.array([5.0, 4.0, 3.0, 4.0, 5.0]),
        "s": np.array([0.0, 2.0, 4.0, 6.0, 8.0]),
    }
    leveePoints = {"x": np.array([2.6, 5.4]), "y": np.array([0.0, 0.0])}

    result = in2DFHyd.assignCrossSectionCoords(leveePoints, crossSection)

    assert result["idLevee"] == [1, 3]
    assert np.all(result["sLevee"] == np.array([2.0, 6.0]))
    assert np.all(result["elevLevee"] == np.array([4.0, 4.0]))

    # levee points lie beyond the range of the cross section
    leveePoints = {"x": np.array([-1.0, 10.0]), "y": np.array([2.4, 7.8])}

    result = in2DFHyd.assignCrossSectionCoords(leveePoints, crossSection)

    assert result["idLevee"] == [1, 3]
    assert np.all(result["sLevee"] == np.array([2.0, 6.0]))
    assert np.all(result["elevLevee"] == np.array([4.0, 4.0]))

    # levee points share the same location
    leveePoints = {"x": np.array([5.0, 5.0]), "y": np.array([0.0, 0.0])}

    with pytest.raises(ValueError, match=r"The two levee points.*"):
        in2DFHyd.assignCrossSectionCoords(leveePoints, crossSection)


def test_getHydrograph_computesReleaseVolume(tmp_path):
    """Check the release volume for each interval without a deprecated array-to-scalar cast."""
    inputDir = tmp_path / "Inputs"
    hydrDir = inputDir / "HYDR"
    hydrDir.mkdir(parents=True)
    pd.DataFrame({"timestep": [0.0, 1.0, 2.0], "discharge": [0.0, 2.0, 4.0]}).to_csv(
        hydrDir / "hydro.csv", index=False
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        hydrograph = in2DFHyd.getHydrograph(inputDir)

    assert np.allclose(hydrograph["relVol"], [1.0, 3.0])


def test_assignRasterCoords():
    """Check nearest raster coordinates are assigned to the
    starting and ending point of the release line"""

    cellSize = 2.0
    xllcenter = 0.0
    yllcenter = 0.0
    releaseLine = {"x": np.array([1.0, 8.0]), "y": np.array([5.0, 5.0])}

    result = in2DFHyd.assignRasterCoords(cellSize, xllcenter, yllcenter, releaseLine)

    assert np.all(result["xRaster"] == np.array([0.0, 8.0]))
    assert np.all(result["yRaster"] == np.array([4.0, 4.0]))

def test_computeSubArea():
    """Check computation of subarea at the boundaries of a wetted cross section"""

    elevation = np.array([4.0, 3.0, 2.0, 1.0, 0.0, 1.0, 2.0, 3.0, 4.0])
    csz = 1.0
    distance = np.arange(0.0, len(elevation) * 2, csz)
    surfElev = 2.5
    idLevee = np.array([0, 8])
    wetCellIdx = np.array([2, 6])

    # starting point
    idx = 0
    subArea, dx = in2DFHyd.computeSubArea(elevation, distance, surfElev, idLevee, wetCellIdx, idx)

    dElev = surfElev - 2.0
    subAreaTest = 0.5 * 0.5 * csz * dElev # half area of a rectangle

    assert subArea == subAreaTest
    assert dx == csz / 2

    # ending point
    surfElev = 1.75
    idx = -1
    wetCellIdx = np.array([3, 5])
    subArea, dx = in2DFHyd.computeSubArea(elevation, distance, surfElev, idLevee, wetCellIdx, idx)

    dElev = surfElev - 1.0
    subAreaTest = 0.5 * 0.75 * csz * dElev # half area of a rectangle

    assert subArea == subAreaTest
    assert dx == csz * 0.75

    # idx has an invalid value
    idx = 2

    with pytest.raises(ValueError, match="idx must be 0 or -1"):
            in2DFHyd.computeSubArea(elevation, distance, surfElev, idLevee, wetCellIdx, idx)
