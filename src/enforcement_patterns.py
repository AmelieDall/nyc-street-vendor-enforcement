"""
Functions to better understand enforcement patterns 
"""

from scipy.stats import gaussian_kde
import numpy as np
import matplotlib.pyplot as plt

def plot_kde_map(points_gdf, boundary_gdf, title, ax=None, cmap='hot_r',
                 bandwidth=None, grid_size=500, point_overlay=False,
                 point_alpha=0.05, point_size=0.3):

    if points_gdf.crs != boundary_gdf.crs:
        points_gdf = points_gdf.to_crs(boundary_gdf.crs)

    valid_mask = points_gdf.geometry.notna() & points_gdf.geometry.is_valid
    coords = np.array([[geom.x, geom.y] for geom in points_gdf.geometry[valid_mask]])
    finite_mask = np.isfinite(coords).all(axis=1)
    coords = coords[finite_mask]

    if coords.shape[0] == 0:
        raise ValueError('No valid points to plot')

    x, y = coords[:, 0], coords[:, 1]
    kde = gaussian_kde(np.vstack([x, y]), bw_method=bandwidth)

    xmin, ymin, xmax, ymax = boundary_gdf.total_bounds
    xi = np.linspace(xmin, xmax, grid_size)
    yi = np.linspace(ymin, ymax, grid_size)
    xx, yy = np.meshgrid(xi, yi)
    zz = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)

    # Use provided ax or create a new one
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 10))
    else:
        fig = ax.get_figure()

    im = ax.imshow(zz, extent=[xmin, xmax, ymin, ymax],
                   origin='lower', cmap=cmap, aspect='equal')
    boundary_gdf.boundary.plot(ax=ax, color='black', linewidth=0.4, alpha=0.6)

    if point_overlay:
        points_gdf.plot(ax=ax, color='black', markersize=point_size, alpha=point_alpha)

    plt.colorbar(im, ax=ax, shrink=0.6, label='Estimated Density')
    ax.set_title(title, fontweight='bold', fontsize=14)
    ax.set_axis_off()

    return fig