"""Small command line interface for GEMC output analysis."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Read and plot GEMC CSV or ROOT output.")
	parser.add_argument("path", help="Output file, ROOT file, CSV file, or CSV rootname.")
	parser.add_argument("variable", nargs="?", help="Variable to plot, for example 'totEdep'.")
	parser.add_argument(
		"--plot",
		choices=("histogram", "yvsx"),
		default="histogram",
		help="Plot type. Default: histogram.",
	)
	parser.add_argument(
		"--kind",
		choices=("auto", "csv", "root"),
		default="auto",
		help="Input format. Default: auto.",
	)
	parser.add_argument(
		"--data",
		choices=("digitized", "true_info", "generated_tracked"),
		default="digitized",
		help="Data stream to plot. Default: digitized.",
	)
	parser.add_argument("--detector", help="Detector/tree name to select.")
	parser.add_argument("--bins", type=int, default=30, help="Plot bin count. Default: 30.")
	parser.add_argument("--x", default="avgx", help="X coordinate column for --plot yvsx. Default: avgx.")
	parser.add_argument("--y", default="avgy", help="Y coordinate column for --plot yvsx. Default: avgy.")
	parser.add_argument("--xlim", nargs=2, type=float, metavar=("LOW", "HIGH"), help="X axis limits.")
	parser.add_argument("--ylim", nargs=2, type=float, metavar=("LOW", "HIGH"), help="Y axis limits.")
	parser.add_argument(
		"--position-unit",
		choices=("mm", "cm"),
		default="cm",
		help="Position unit for --plot yvsx limits and labels. Default: cm.",
	)
	parser.add_argument("--linear-y", action="store_true", help="Use a linear y axis instead of log scale.")
	parser.add_argument("--save", type=Path, help="Write the figure to this path instead of showing it.")
	return parser


def main(argv: list[str] | None = None) -> None:
	args = build_parser().parse_args(argv)

	if args.save:
		import matplotlib

		matplotlib.use("Agg")

	from .plotting import available_variables, plot_variable, plot_y_vs_x
	from .readers import read_output

	output = read_output(args.path, kind=args.kind)

	if not args.variable and args.plot == "histogram":
		print(output.summary())
		for stream in ("digitized", "true_info", "generated_tracked"):
			if not output.available(stream):
				continue
			variables = available_variables(output, data=stream)
			if variables:
				print(f"plottable {stream}: " + ", ".join(sorted(variables)))
		return

	if args.plot == "yvsx":
		frame = output.get_frame(data=args.data, detector=args.detector)
		fig, _ = plot_y_vs_x(
			frame,
			x=args.x,
			y=args.y,
			bins=args.bins,
			xlim=tuple(args.xlim) if args.xlim else None,
			ylim=tuple(args.ylim) if args.ylim else None,
			position_unit=args.position_unit,
		)
	else:
		fig, _ = plot_variable(
			output,
			args.variable,
			data=args.data,
			detector=args.detector,
			bins=args.bins,
			xlim=tuple(args.xlim) if args.xlim else None,
			logy=not args.linear_y,
		)

	if args.save:
		fig.savefig(args.save, bbox_inches="tight")
	else:
		from matplotlib import pyplot as plt

		plt.show()
