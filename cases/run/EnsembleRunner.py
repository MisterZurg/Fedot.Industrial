import pandas as pd

from cases.run.ExperimentRunner import ExperimentRunner
from cases.run.QuantileRunner import StatsRunner
from cases.run.SSARunner import SSARunner
from cases.run.SignalRunner import SignalRunner
from cases.run.TopologicalRunner import TopologicalRunner


class EnsembleRunner(ExperimentRunner):
    def __init__(self,
                 feature_generator_dict: dict = None,
                 list_of_dataset: list = None,
                 launches: int = 3,
                 metrics_name: list = ['f1', 'roc_auc', 'accuracy', 'logloss', 'precision'],
                 fedot_params: dict = None,
                 list_of_generators=None
                 ):
        self.list_of_generators = list_of_generators
        super().__init__(feature_generator_dict, list_of_dataset, launches, metrics_name, fedot_params)

        self.generator_dict = dict(quantile=StatsRunner,
                                   window_quantile=StatsRunner,
                                   wavelet=SignalRunner,
                                   spectral=SSARunner,
                                   spectral_window=SSARunner,
                                   topological=TopologicalRunner,
                                   ensemble=EnsembleRunner)

    def extract_features(self, input_data):
        return self.ensemble_features(input_data)

    def ensemble_features(self, input_data):
        features = list()
        for generator_name, generator in self.list_of_generators.items():
            features_df = generator.extract_features(input_data)
            features.append(features_df)

        return pd.concat(features, axis=1)
