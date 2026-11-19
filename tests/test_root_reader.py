"""ROOT reader regressions runnable without the optional uproot dependency."""

from contextlib import nullcontext
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from pygemc.analyzer.readers import _tree_to_frame, read_root_output


class RootTree:
    """Provide the NumPy-style entry arrays consumed by the ROOT reader."""

    def __init__(self, **columns):
        self.columns = {name: np.array(values, dtype=object) for name, values in columns.items()}
        self.num_entries = len(next(iter(columns.values())))

    def arrays(self, *, library):
        assert library == "np"
        return self.columns


class RootReaderTests(unittest.TestCase):
    def test_sparse_truth_and_digitized_entries_keep_their_own_event_keys(self):
        trees = {
            "event_header;1": RootTree(g4localEventNumber=[[17], [18], [19]], threadID=[[0], [0], [0]]),
            "true_info_A;1": RootTree(
                g4localEventNumber=[[17], [19]], threadID=[[0], [0]], energy=[[1.0, 2.0], [3.0]]),
            "digitized_A;1": RootTree(g4localEventNumber=[[19]], threadID=[[0]], energy=[[4.0, 5.0]]),
            "digitized_B;1": RootTree(g4localEventNumber=[[18]], threadID=[[0]], energy=[[6.0]]),
        }
        uproot = SimpleNamespace(open=lambda path: nullcontext(trees))
        with patch.dict(sys.modules, {"uproot": uproot}):
            output = read_root_output("sparse.root")

        self.assertEqual(output.headers["event_header"]["g4localEventNumber"].tolist(), [17, 18, 19])
        self.assertEqual(output.true_info["A"]["g4localEventNumber"].tolist(), [17, 17, 19])
        self.assertEqual(output.digitized["A"]["g4localEventNumber"].tolist(), [19, 19])
        self.assertEqual(output.digitized["B"]["g4localEventNumber"].tolist(), [18])
        self.assertEqual(output.true_info["A"]["energy"].tolist(), [1.0, 2.0, 3.0])
        self.assertEqual(output.digitized["A"]["threadID"].tolist(), [0, 0])

    def test_repeated_local_event_numbers_keep_distinct_worker_ids(self):
        frame = _tree_to_frame(RootTree(
            g4localEventNumber=[[17], [17]], threadID=[[0], [1]], energy=[[1.0, 2.0], [3.0, 4.0]]))

        self.assertEqual(list(zip(frame["g4localEventNumber"], frame["threadID"])),
                         [(17, 0), (17, 0), (17, 1), (17, 1)])

    def test_scalar_event_metadata_is_broadcast_without_repeating_short_hit_vectors(self):
        frame = _tree_to_frame(RootTree(
            g4localEventNumber=[19], threadID=[1], energy=[[1.0, 2.0]], pid=[[11]]))

        self.assertEqual(frame["g4localEventNumber"].tolist(), [19, 19])
        self.assertEqual(frame["threadID"].tolist(), [1, 1])
        self.assertEqual(frame.loc[0, "pid"], 11)
        self.assertTrue(pd.isna(frame.loc[1, "pid"]))

    def test_missing_metadata_does_not_inherit_the_previous_event(self):
        frame = _tree_to_frame(RootTree(
            g4localEventNumber=[[17], []], threadID=[[0], []], energy=[[1.0], [2.0, 3.0]]))

        self.assertEqual(frame.loc[0, "g4localEventNumber"], 17)
        self.assertTrue(frame.loc[1:, ["g4localEventNumber", "threadID"]].isna().all().all())

    def test_legacy_and_run_integrated_trees_keep_their_existing_schema(self):
        legacy = _tree_to_frame(RootTree(energy=[[1.0, 2.0], [3.0]], pid=[[11], [13]]))
        integrated = _tree_to_frame(RootTree(dose=[[10.0]]))

        self.assertEqual(list(legacy.columns), ["energy", "pid"])
        self.assertEqual(legacy["energy"].tolist(), [1.0, 2.0, 3.0])
        self.assertTrue(pd.isna(legacy.loc[1, "pid"]))
        self.assertEqual(list(integrated.columns), ["dose"])
        self.assertEqual(integrated["dose"].tolist(), [10.0])


if __name__ == "__main__":
    unittest.main()
