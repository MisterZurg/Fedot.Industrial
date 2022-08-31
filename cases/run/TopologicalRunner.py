from core.models.topological.TFE import TopologicalFeaturesExtractor, PersistenceDiagramsExtractor, \
    HolesNumberFeature, MaxHoleLifeTimeFeature, RelevantHolesNumber, AverageHoleLifetimeFeature, \
    SumHoleLifetimeFeature, PersistenceEntropyFeature, SimultaneousAliveHolesFeature, \
    AveragePersistenceLandscapeFeature, BettiNumbersSumFeature, RadiusAtMaxBNFeature
from cases.run.ExperimentRunner import ExperimentRunner
from core.models.topological.TDA import Topological
from core.operation.utils.utils import *

from gtda.time_series import SingleTakensEmbedding

import timeit


dict_of_dataset = dict
dict_of_win_list = dict

PERSISTENCE_DIAGRAM_FEATURES = {'HolesNumberFeature': HolesNumberFeature(),
                                'MaxHoleLifeTimeFeature': MaxHoleLifeTimeFeature(),
                                'RelevantHolesNumber': RelevantHolesNumber(),
                                'AverageHoleLifetimeFeature': AverageHoleLifetimeFeature(),
                                'SumHoleLifetimeFeature': SumHoleLifetimeFeature(),
                                'PersistenceEntropyFeature': PersistenceEntropyFeature(),
                                'SimultaneousAliveHolesFeature': SimultaneousAliveHolesFeature(),
                                'AveragePersistenceLandscapeFeature': AveragePersistenceLandscapeFeature(),
                                'BettiNumbersSumFeature': BettiNumbersSumFeature(),
                                'RadiusAtMaxBNFeature': RadiusAtMaxBNFeature()}


class TopologicalRunner(ExperimentRunner):
    """
    Class for extracting topological features from time series data
    """
    def __init__(self, topological_params: dict,
                 list_of_dataset: list = None):
        super().__init__(list_of_dataset)
        self.topological_extractor = Topological(**topological_params)
        self.TE_dimension = None
        self.TE_time_delay = None

    def generate_topological_features(self, ts_data: pd.DataFrame) -> pd.DataFrame:
        start = timeit.default_timer()

        if not self.TE_dimension and not self.TE_time_delay:
            single_ts = ts_data.loc[0]
            self.TE_dimension, self.TE_time_delay = self.get_embedding_params(single_time_series=single_ts)
            self.logger.info(f'TE_delay: {self.TE_time_delay}, TE_dimension: {self.TE_dimension} are selected')

        persistence_diagram_extractor = PersistenceDiagramsExtractor(takens_embedding_dim=self.TE_dimension,
                                                                     takens_embedding_delay=self.TE_time_delay,
                                                                     homology_dimensions=(0, 1),
                                                                     parallel=True)

        feature_extractor = TopologicalFeaturesExtractor(persistence_diagram_extractor=persistence_diagram_extractor,
                                                         persistence_diagram_features=PERSISTENCE_DIAGRAM_FEATURES)

        ts_data_transformed = feature_extractor.fit_transform(ts_data.values)
        ts_data_transformed = delete_col_by_var(ts_data_transformed)

        time_elapsed = round(timeit.default_timer() - start, 2)
        self.logger.info(f'Time spent on feature generation - {time_elapsed} sec')
        return ts_data_transformed

    def extract_features(self, ts_data: pd.DataFrame, dataset_name: str = None):
        self.logger.info('Topological features extraction started')
        return self.generate_topological_features(ts_data=ts_data)

    @staticmethod
    def get_embedding_params(single_time_series):
        embedder = SingleTakensEmbedding(parameters_type="search",
                                         time_delay=10,
                                         dimension=10)
        embedder.fit_transform(single_time_series)
        return embedder.dimension_, embedder.time_delay_
