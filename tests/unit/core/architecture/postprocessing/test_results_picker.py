import os

import pandas as pd
import pytest

from fedot_ind.api.utils.path_lib import PROJECT_PATH
from fedot_ind.core.architecture.postprocessing.results_picker import ResultsPicker

results_path = os.path.join(PROJECT_PATH, 'tests/data/classification_results')


def test_run_basic():
    picker = ResultsPicker(path=results_path)
    proba_dict, metric_dict = picker.run()
    assert isinstance(proba_dict, dict)
    assert isinstance(metric_dict, dict)


def test_run_return_dataframe():
    picker = ResultsPicker(path=results_path)
    result_dataframe = picker.run(get_metrics_df=True, add_info=True)
    assert isinstance(result_dataframe, pd.DataFrame)
