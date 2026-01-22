import numpy as np
import matplotlib.pyplot as plt
import logging

log = logging.getLogger(__name__)

class HillshadePlotter:
    def __init__(self):
        pass

    @staticmethod
    def hillshade(array, azimuth, angle_altitude):
        """Creates a shaded relief file from a DEM."""
        from numpy import gradient, pi, arctan, arctan2, sin, cos, sqrt

        x, y = gradient(array)
        slope = pi / 2.0 - arctan(sqrt(x * x + y * y))
        aspect = arctan2(-x, y)
        azimuthrad = azimuth * pi / 180.0
        altituderad = angle_altitude * pi / 180.0

        shaded = (
            sin(altituderad) * sin(slope)
            + cos(altituderad) * cos(slope) * cos(azimuthrad - aspect)
        )
        return 255 * (shaded + 1) / 2

    def plot(self, depo_path, dem_path, eventname, outdir):
        """
        Plots the deposition result on the hillshade based on the DEM.
        """
        # Read DEM and deposition data
        with open(dem_path, "r") as dem_f:
            dem_header = dem_f.readlines()[:6]

        dem_header = [item.strip().split()[-1] for item in dem_header]
        dem_cols = int(dem_header[0])
        dem_rows = int(dem_header[1])
        dem_xll = float(dem_header[2])
        dem_yll = float(dem_header[3])
        dem_cs = float(dem_header[4])
        dem_nodata = float(dem_header[5])

        dem_array = np.loadtxt(dem_path, dtype=np.float64, skiprows=6)
        dem_array[dem_array == dem_nodata] = np.nan

        # Generate the hillshade for visualization
        hs_array = self.hillshade(dem_array, azimuth=34, angle_altitude=45)

        # Read deposition data
        depo_array = np.loadtxt(depo_path, dtype=np.float64, skiprows=6)
        depo_array = np.ma.masked_where(depo_array < 0.005, depo_array)

        # Plot the results
        cmap = plt.cm.viridis  
        # cmap.set_bad(color="white")  # Set color for masked values
        fig, ax = plt.subplots(figsize=(4.27, 3.2))
        ax.set_title(f"Deposition - {eventname}")
        dem_extent = [
            dem_xll,
            dem_xll + dem_cols * dem_cs,
            dem_yll,
            dem_yll + dem_rows * dem_cs,
        ]
        # Plot hillshade
        ax.imshow(hs_array, extent=dem_extent, cmap="Greys")
        # Overlay deposition data
        img_plot = ax.imshow(depo_array, extent=dem_extent, cmap=cmap)
        # Add colorbar
        cbar = plt.colorbar(img_plot, orientation="vertical", aspect=14)
        cbar.set_label("Deposition heights [m]")
        # Save the plot
        output_plot_path = outdir / f"{eventname}_deposition.png"
        fig.savefig(output_plot_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        log.info(f"Plot saved to {output_plot_path}")
