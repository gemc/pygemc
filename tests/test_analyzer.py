import matplotlib
import pandas as pd

matplotlib.use("Agg")

from pygemc.analyzer.cli import main as analyzer_main
from pygemc.analyzer.plotting import plot_y_vs_x


def test_plot_y_vs_x_uses_cm_limits():
	frame = pd.DataFrame({"avgx": [-100.0, 0.0, 100.0], "avgy": [-50.0, 0.0, 50.0]})

	fig, ax = plot_y_vs_x(frame, xlim=(-20, 20), ylim=(-20, 20), position_unit="cm")

	assert ax.get_xlim() == (-20.0, 20.0)
	assert ax.get_ylim() == (-20.0, 20.0)
	assert ax.get_xlabel() == "Average X Position [cm]"
	assert ax.get_ylabel() == "Average Y Position [cm]"
	fig.clf()


def test_analyzer_cli_saves_y_vs_x_plot(tmp_path):
	csv_path = tmp_path / "hits_t0_true_info.csv"
	csv_path.write_text("avgx,avgy\n-100,-50\n0,0\n100,50\n")
	output_path = tmp_path / "hits_y_vs_x.png"

	analyzer_main(
		[
			str(csv_path),
			"--kind",
			"csv",
			"--data",
			"true_info",
			"--plot",
			"yvsx",
			"--xlim",
			"-20",
			"20",
			"--ylim",
			"-20",
			"20",
			"--save",
			str(output_path),
		]
	)

	assert output_path.exists()
	assert output_path.stat().st_size > 0
