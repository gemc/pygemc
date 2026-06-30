import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from pygemc.analyzer.cli import main as analyzer_main
from pygemc.analyzer.plotting import available_variables, plot_variable, plot_y_vs_x
from pygemc.analyzer.readers import read_output

GENERATED_TRACKED_CSV = (
	"evn, timestamp, thread_id, bank, name, pid, type, multiplicity, p, theta, phi, vx, vy, vz\n"
	"1, 0, 0, generated_tracked, e-, 11, primary, 1, 1500, 0.10, 0.20, 0, 0, 0\n"
	"2, 0, 0, generated_tracked, e-, 11, primary, 1, 2500, 0.30, 0.40, 0, 0, 0\n"
)


def test_plot_y_vs_x_uses_cm_limits():
	frame = pd.DataFrame({"avgx": [-100.0, 0.0, 100.0], "avgy": [-50.0, 0.0, 50.0]})

	fig, ax = plot_y_vs_x(frame, xlim=(-20, 20), ylim=(-20, 20), position_unit="cm")

	assert ax.get_xlim() == (-20.0, 20.0)
	assert ax.get_ylim() == (-20.0, 20.0)
	assert ax.get_xlabel() == "Average X Position [cm]"
	assert ax.get_ylabel() == "Average Y Position [cm]"
	fig.clf()


def test_plot_y_vs_x_filters_pid():
	frame = pd.DataFrame(
		{"avgx": [-100.0, 0.0, 100.0], "avgy": [-50.0, 0.0, 50.0], "pid": [11, 11, 13]}
	)

	fig, ax = plot_y_vs_x(frame, pid=11)

	assert np.asarray(ax.collections[0].get_array()).sum() == 2
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


def test_reads_generated_tracked_kinematics(tmp_path):
	csv_path = tmp_path / "beam_generated_tracked.csv"
	csv_path.write_text(GENERATED_TRACKED_CSV)

	output = read_output(csv_path, kind="csv")

	assert output.available("generated_tracked") == [csv_path.stem]
	variables = available_variables(output, data="generated_tracked")
	assert variables["p"] == "Momentum (MeV)"
	assert variables["theta"] == "Theta (rad)"
	assert variables["phi"] == "Phi (rad)"


def test_plot_variable_falls_back_to_generated_tracked(tmp_path):
	from pygemc.analyzer.dataset import GemcOutput

	gen_path = tmp_path / "beam_generated_tracked.csv"
	gen_path.write_text(GENERATED_TRACKED_CSV)
	generated = pd.read_csv(gen_path, skipinitialspace=True)
	digitized = pd.DataFrame({"evn": [1, 2], "totEdep": [3.0, 4.0]})
	output = GemcOutput(digitized={"csv": digitized}, generated_tracked={"csv": generated})

	# 'p' is absent from the digitized stream, so it is taken from generated_tracked.
	fig, ax = plot_variable(output, "p", data="digitized", group_by=None)
	assert ax.get_xlabel() == "Momentum (MeV)"
	fig.clf()


def test_plot_variable_fallback_when_selected_stream_empty(tmp_path):
	# Only the generated_tracked file is loaded, so the default 'digitized' stream is empty.
	csv_path = tmp_path / "beam_generated_tracked.csv"
	csv_path.write_text(GENERATED_TRACKED_CSV)
	output = read_output(csv_path, kind="csv")

	fig, ax = plot_variable(output, "theta", group_by=None)
	assert ax.get_xlabel() == "Theta (rad)"
	fig.clf()


def test_analyzer_cli_summary_lists_plottable_quantities(tmp_path, capsys):
	csv_path = tmp_path / "beam_generated_tracked.csv"
	csv_path.write_text(GENERATED_TRACKED_CSV)

	analyzer_main([str(csv_path), "--kind", "csv"])

	out = capsys.readouterr().out
	assert "plottable generated_tracked:" in out
	assert "theta" in out
	assert "phi" in out


def test_original_track_deltas_are_available_for_matching_pid(tmp_path):
	csv_path = tmp_path / "hits_true_info.csv"
	csv_path.write_text(
		"pid,opid,px,py,pz,opx,opy,opz\n"
		"11,11,8,0,0,10,0,0\n"
		f"11,11,{np.cos(np.deg2rad(-179))},{np.sin(np.deg2rad(-179))},0,"
		f"{np.cos(np.deg2rad(179))},{np.sin(np.deg2rad(179))},0\n"
		"211,11,0,3,4,0,0,10\n"
	)

	output = read_output(csv_path, kind="csv")
	frame = output.get_frame(data="true_info")
	variables = available_variables(output, data="true_info")

	assert variables["delta_p"] == "Delta Momentum (MeV)"
	assert variables["delta_theta"] == "Delta Theta (rad)"
	assert variables["delta_phi"] == "Delta Phi (rad)"
	assert frame.loc[0, "delta_p"] == -2.0
	assert np.isclose(frame.loc[1, "delta_phi"], np.deg2rad(2))
	assert frame.loc[2, ["delta_p", "delta_theta", "delta_phi"]].isna().all()

	fig, ax = plot_variable(output, "delta_p", data="true_info", group_by=None)
	assert ax.get_xlabel() == "Delta Momentum (MeV)"
	fig.clf()


def test_original_track_deltas_require_complete_csv_quantities(tmp_path):
	csv_path = tmp_path / "hits_true_info.csv"
	csv_path.write_text("pid,opid,px,py,pz\n11,11,1,0,0\n")

	output = read_output(csv_path, kind="csv")

	assert "delta_p" not in available_variables(output, data="true_info")


def test_plot_variable_filters_original_track_delta_by_pid(tmp_path):
	csv_path = tmp_path / "hits_true_info.csv"
	csv_path.write_text(
		"pid,opid,px,py,pz,opx,opy,opz\n"
		"11,11,8,0,0,10,0,0\n"
		"11,11,7,0,0,10,0,0\n"
		"13,13,6,0,0,10,0,0\n"
	)
	output_path = tmp_path / "electron_delta_p.png"

	analyzer_main(
		[
			str(csv_path),
			"delta_p",
			"--data",
			"true_info",
			"--pid",
			"11",
			"--save",
			str(output_path),
		]
	)

	assert output_path.exists()
	fig, ax = plot_variable(read_output(csv_path), "delta_p", data="true_info", pid=11, group_by=None)
	assert sum(patch.get_height() for patch in ax.patches) == 2
	fig.clf()


def test_analyzer_cli_reports_empty_delta_pid_filter_without_error(tmp_path, capsys):
	csv_path = tmp_path / "hits_true_info.csv"
	csv_path.write_text(
		"pid,opid,px,py,pz,opx,opy,opz\n"
		"11,2212,1,0,0,0,0,10\n"
		"2212,2212,0,0,8,0,0,10\n"
	)

	analyzer_main([str(csv_path), "delta_theta", "--data", "true_info", "--pid", "11"])

	captured = capsys.readouterr()
	assert (
		"No plot created: Column 'delta_theta' has no numeric values to plot after filtering pid 11."
		in captured.out
	)
	assert captured.err == ""
