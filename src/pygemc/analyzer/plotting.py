"""Plotting helpers for GEMC output tables."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .dataset import GemcOutput


DEFAULT_LABELS: Mapping[str, str] = {
	"totEdep": "Total Energy Deposit (MeV)",
	"totalEDeposited": "Total Energy Deposited (MeV)",
	"etot": "Total Energy (MeV)",
	"dose": "Dose",
	"time": "Time",
	"avgTime": "Average Time",
	"E": "Energy (MeV)",
	"totalE": "Total Energy (MeV)",
	"p": "Momentum (MeV)",
	"momentum": "Momentum (MeV)",
	"theta": "Theta (rad)",
	"phi": "Phi (rad)",
	"delta_p": "Delta Momentum (MeV)",
	"delta_theta": "Delta Theta (rad)",
	"delta_phi": "Delta Phi (rad)",
	"multiplicity": "Multiplicity",
	"vx": "Track Vertex X (mm)",
	"vy": "Track Vertex Y (mm)",
	"vz": "Track Vertex Z (mm)",
	"mvx": "Mother Track Vertex X (mm)",
	"mvy": "Mother Track Vertex Y (mm)",
	"mvz": "Mother Track Vertex Z (mm)",
	"mtid": "Mother Track ID",
	"avgx": "Average X Position",
	"avgy": "Average Y Position",
	"avgz": "Average Z Position",
}

VARIABLE_ALIASES: Mapping[str, tuple[str, ...]] = {
	"momentum": ("p",),
	"E": ("totalE", "etot"),
	"totalEDeposited": ("totEdep",),
	"etot": ("totalE",),
	"track_vx": ("vx",),
	"track_vy": ("vy",),
	"track_vz": ("vz",),
	"mother_vx": ("mvx",),
	"mother_vy": ("mvy",),
	"mother_vz": ("mvz",),
}


GENERATED_FALLBACK_STREAM = "generated_tracked"


def available_variables(
	output: GemcOutput | pd.DataFrame,
	*,
	data: str = "digitized",
	detector: str | None = None,
) -> dict[str, str]:
	"""Return the numeric quantities available to plot, mapped to axis labels.

	``output`` may be a :class:`GemcOutput` or a DataFrame. When it is a
	``GemcOutput`` the ``data`` stream is selected, for example ``digitized``,
	``true_info``, or ``generated_tracked``. The ``generated_tracked`` stream
	exposes the generated particle kinematics such as ``p``, ``theta``, and ``phi``.
	"""

	frame = output.get_frame(data=data, detector=detector) if isinstance(output, GemcOutput) else output
	numeric = frame.select_dtypes(include="number").columns
	return {column: DEFAULT_LABELS.get(column, column) for column in numeric}


def plot_variable(
	output: GemcOutput | pd.DataFrame,
	variable: str,
	*,
	data: str = "digitized",
	detector: str | None = None,
	bins: int = 30,
	xlim: tuple[float, float] | None = None,
	pid: int | None = None,
	group_by: str | None = "pid",
	logy: bool = True,
	ax: plt.Axes | None = None,
	show: bool = False,
	**hist_kwargs: Any,
) -> tuple[plt.Figure, plt.Axes]:
	"""Plot a variable selected by string.

	``data`` selects the GEMC stream, one of ``digitized``, ``true_info``, or
	``generated_tracked`` when ``output`` is a :class:`GemcOutput`. When the
	selected stream lacks ``variable`` (for example the generated ``theta``,
	``phi``, or ``p``), the ``generated_tracked`` stream is used as a fallback.
	When ``pid`` is set, only rows with that particle ID are plotted.
	"""

	if isinstance(output, GemcOutput):
		frame = _select_frame(output, variable, data=data, detector=detector)
	else:
		frame = output
	return plot_histogram(
		frame,
		variable,
		bins=bins,
		xlim=xlim,
		pid=pid,
		group_by=group_by,
		logy=logy,
		ax=ax,
		show=show,
		**hist_kwargs,
	)


def plot_y_vs_x(
	frame: pd.DataFrame,
	*,
	x: str = "avgx",
	y: str = "avgy",
	bins: int = 80,
	xlim: tuple[float, float] | None = None,
	ylim: tuple[float, float] | None = None,
	position_unit: str = "cm",
	pid: int | None = None,
	ax: plt.Axes | None = None,
	show: bool = False,
	**hist_kwargs: Any,
) -> tuple[plt.Figure, plt.Axes]:
	"""Plot a 2D hit-position map using ``y`` versus ``x`` coordinates.

	When ``pid`` is set, only rows with that particle ID are plotted.
	"""

	frame = _filter_pid(frame, pid)

	x = _resolve_variable(frame, x)
	y = _resolve_variable(frame, y)

	x_values = pd.to_numeric(frame[x], errors="coerce")
	y_values = pd.to_numeric(frame[y], errors="coerce")
	values = pd.DataFrame({"x": x_values, "y": y_values}).dropna()
	if values.empty:
		raise ValueError(f"Columns '{x}' and '{y}' have no numeric values to plot.")

	scale = _position_scale(position_unit)
	values = values * scale

	if ax is None:
		fig, ax = plt.subplots(figsize=(5.2, 4.8))
	else:
		fig = ax.figure

	hist_defaults = {"cmap": "viridis"}
	hist_defaults.update(hist_kwargs)
	hist = ax.hist2d(
		values["x"],
		values["y"],
		bins=bins,
		range=_hist2d_range(values, xlim, ylim),
		**hist_defaults,
	)
	cbar = fig.colorbar(hist[3], ax=ax)
	cbar.set_label("Hits / bin")

	if xlim is not None:
		ax.set_xlim(xlim)
	if ylim is not None:
		ax.set_ylim(ylim)

	unit_label = f" [{position_unit}]" if position_unit else ""
	ax.set_xlabel(f"{DEFAULT_LABELS.get(x, x)}{unit_label}", fontsize=12)
	ax.set_ylabel(f"{DEFAULT_LABELS.get(y, y)}{unit_label}", fontsize=12)
	ax.set_title(f"{DEFAULT_LABELS.get(y, y)} vs {DEFAULT_LABELS.get(x, x)}", fontsize=14)
	fig.tight_layout(pad=0.4)

	if show:
		plt.show()

	return fig, ax


def plot_histogram(
	frame: pd.DataFrame,
	variable: str,
	*,
	bins: int = 30,
	xlim: tuple[float, float] | None = None,
	pid: int | None = None,
	group_by: str | None = "pid",
	logy: bool = True,
	ax: plt.Axes | None = None,
	show: bool = False,
	**hist_kwargs: Any,
) -> tuple[plt.Figure, plt.Axes]:
	"""Plot one numeric variable as a histogram, optionally grouped by a column and filtered by ``pid``."""

	frame = _filter_pid(frame, pid)
	variable = _resolve_variable(frame, variable)

	values = pd.to_numeric(frame[variable], errors="coerce").dropna()
	if values.empty:
		pid_context = f" after filtering pid {pid}" if pid is not None else ""
		raise ValueError(f"Column '{variable}' has no numeric values to plot{pid_context}.")

	if ax is None:
		fig, ax = plt.subplots(figsize=(10, 6))
	else:
		fig = ax.figure

	data_range = values.clip(*xlim) if xlim is not None else values
	if data_range.min() == data_range.max():
		bin_edges = bins
	else:
		bin_edges = np.linspace(data_range.min(), data_range.max(), bins + 1)

	hist_defaults = {"alpha": 0.7, "edgecolor": "white", "linewidth": 0.5}
	hist_defaults.update(hist_kwargs)

	if group_by and group_by in frame.columns:
		colors = list(mcolors.TABLEAU_COLORS.values())
		for index, group_value in enumerate(sorted(frame[group_by].dropna().unique())):
			subset = pd.to_numeric(frame.loc[frame[group_by] == group_value, variable], errors="coerce").dropna()
			ax.hist(
				subset,
				bins=bin_edges,
				label=f"{group_by} {group_value}",
				color=colors[index % len(colors)],
				**hist_defaults,
			)
		ax.legend(title=group_by)
	else:
		ax.hist(values, bins=bin_edges, **hist_defaults)

	if xlim is not None:
		ax.set_xlim(xlim)
	if logy:
		ax.set_yscale("log")

	ax.set_xlabel(DEFAULT_LABELS.get(variable, variable), fontsize=12)
	ax.set_ylabel("Counts", fontsize=12)
	ax.set_title(f"{DEFAULT_LABELS.get(variable, variable)} Histogram", fontsize=14)
	fig.tight_layout()

	if show:
		plt.show()

	return fig, ax


def _hist2d_range(
	values: pd.DataFrame,
	xlim: tuple[float, float] | None,
	ylim: tuple[float, float] | None,
) -> list[tuple[float, float]] | None:
	if xlim is None and ylim is None:
		return None

	xrange = xlim if xlim is not None else (float(values["x"].min()), float(values["x"].max()))
	yrange = ylim if ylim is not None else (float(values["y"].min()), float(values["y"].max()))
	return [xrange, yrange]


def _position_scale(position_unit: str) -> float:
	if position_unit == "mm":
		return 1.0
	if position_unit == "cm":
		return 0.1
	raise ValueError("position_unit must be one of: 'mm', 'cm'")


def _filter_pid(frame: pd.DataFrame, pid: int | None) -> pd.DataFrame:
	if pid is None:
		if frame.empty:
			raise ValueError("Selected data table is empty.")
		return frame
	if "pid" not in frame.columns:
		raise KeyError("Cannot filter by PID: column 'pid' is not present.")

	filtered = frame.loc[pd.to_numeric(frame["pid"], errors="coerce") == pid]
	if filtered.empty:
		raise ValueError(f"No rows match pid {pid}.")
	return filtered


def _has_variable(frame: pd.DataFrame, variable: str) -> bool:
	if variable in frame.columns:
		return True
	return any(alias in frame.columns for alias in VARIABLE_ALIASES.get(variable, ()))


def _select_frame(output: GemcOutput, variable: str, *, data: str, detector: str | None) -> pd.DataFrame:
	"""Return the frame to plot ``variable`` from.

	The ``data`` stream is preferred. When it is empty/missing or lacks
	``variable``, the ``generated_tracked`` stream is used so the generated
	``p``, ``theta``, and ``phi`` plot even with the default ``data``."""

	try:
		frame = output.get_frame(data=data, detector=detector)
	except (ValueError, KeyError):
		frame = None

	if frame is not None and _has_variable(frame, variable):
		return frame

	if output.available(GENERATED_FALLBACK_STREAM):
		candidate = output.get_frame(data=GENERATED_FALLBACK_STREAM)
		if _has_variable(candidate, variable):
			return candidate

	if frame is not None:
		return frame
	# Nothing matched: re-run the selection so its original error surfaces.
	return output.get_frame(data=data, detector=detector)


def _resolve_variable(frame: pd.DataFrame, variable: str) -> str:
	if variable not in frame.columns:
		for alias in VARIABLE_ALIASES.get(variable, ()):
			if alias in frame.columns:
				return alias
		available = ", ".join(frame.columns)
		raise KeyError(f"Column '{variable}' not found. Available columns: {available}")
	return variable
