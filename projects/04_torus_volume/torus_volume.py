"""Simulate and forecast 15-minute trading volume with periodic features.

Requires NumPy and Matplotlib. Run with: python torus_volume.py
"""

import calendar
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize


def design_matrix(day_angle, month_angle, interactions=False):
    """Build an intercept, two cyclic main effects, and optional products."""
    daily = [np.cos(day_angle), np.sin(day_angle)]
    monthly = [np.cos(month_angle), np.sin(month_angle)]
    columns = [np.ones_like(day_angle), *daily, *monthly]
    if interactions:
        columns.extend(day * month for day in daily for month in monthly)
    return np.column_stack(columns)


def main():
    rng = np.random.default_rng(42)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2025, 7, 1, tzinfo=timezone.utc)
    cutoff = datetime(2025, 1, 1, tzinfo=timezone.utc)
    interval = timedelta(minutes=15)
    timestamps = [start + i * interval for i in range((end - start) // interval)]

    # Each timestamp marks the start of the 15-minute interval we forecast.
    hours = np.array([t.hour + t.minute / 60 for t in timestamps])
    month_days = np.array([calendar.monthrange(t.year, t.month)[1] for t in timestamps])
    month_fraction = (np.array([t.day - 1 for t in timestamps]) + hours / 24) / month_days
    day_angle = 2 * np.pi * hours / 24
    month_angle = 2 * np.pi * month_fraction
    afternoon = np.cos(day_angle - 2 * np.pi * 16 / 24)
    month_turn = np.cos(month_angle)
    volume = (
        100 + 12 * afternoon + 8 * month_turn
        + 24 * afternoon * month_turn + rng.normal(0, 8, len(hours))
    )

    train_size = (cutoff - start) // interval
    train = slice(None, train_size)
    test = slice(train_size, None)
    print(f"Train: 2024 ({train_size:,} intervals)")
    print(f"Test: Jan–Jun 2025 ({len(hours) - train_size:,} intervals)")

    day_grid, month_grid = np.meshgrid(
        np.linspace(0, 2 * np.pi, 121), np.linspace(0, 2 * np.pi, 121)
    )
    surfaces = []
    errors = []
    for name, interactions in [("Additive", False), ("With interactions", True)]:
        features = design_matrix(day_angle, month_angle, interactions)
        weights = np.linalg.lstsq(features[train], volume[train], rcond=None)[0]
        residuals = volume[test] - features[test] @ weights
        rmse = np.sqrt(np.mean(residuals**2))
        errors.append(rmse)
        print(f"{name:18s} test RMSE: {rmse:.2f} volume units")
        grid_features = design_matrix(day_grid.ravel(), month_grid.ravel(), interactions)
        surfaces.append((grid_features @ weights).reshape(day_grid.shape))

    print(f"Relative RMSE reduction: {1 - errors[1] / errors[0]:.1%}")

    # The first angle goes around the ring, the second around its tube.
    ring_radius = 2.3 + 0.8 * np.cos(month_grid)
    x = ring_radius * np.cos(day_grid)
    y = ring_radius * np.sin(day_grid)
    z = 0.8 * np.sin(month_grid)
    cmap = plt.get_cmap("viridis")
    norm = Normalize(vmin=55, vmax=145)
    fig = plt.figure(figsize=(13, 4.6), layout="constrained")
    fig.suptitle("Forecasting simulated 15-minute trading volume", fontsize=16)
    for index, (surface, title) in enumerate(zip(surfaces, ["Additive", "With interactions"]), 1):
        ax = fig.add_subplot(1, 3, index)
        heatmap = ax.pcolormesh(
            day_grid * 24 / (2 * np.pi), month_grid * 100 / (2 * np.pi),
            surface, cmap=cmap, norm=norm, shading="auto",
        )
        ax.set_title(f"{title} model")
        ax.set(xlabel="Time of day (UTC)", ylabel="Position in month (%)",
               xticks=[0, 6, 12, 18, 24], yticks=[0, 25, 50, 75, 100])

    ax = fig.add_subplot(1, 3, 3, projection="3d")
    ax.plot_surface(x, y, z, facecolors=cmap(norm(surfaces[1])),
                    rcount=100, ccount=100, shade=False, linewidth=0)
    ax.set_title("Interaction model on a torus")
    ax.set_box_aspect((1, 1, 0.35))
    ax.view_init(elev=46, azim=38)
    ax.set_axis_off()
    fig.colorbar(heatmap, ax=fig.axes, shrink=0.76, label="Predicted volume (units)")
    output = Path(__file__).with_name("torus_volume.png")
    fig.savefig(output, dpi=160)
    print(f"Plot saved to {output.name}")


if __name__ == "__main__":
    main()
