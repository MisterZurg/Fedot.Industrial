from core.operation.utils.Decorators import exception_decorator
from core.operation.utils.LoggerSingleton import Logger
from core.metrics.metrics_implementation import *
from core.operation.utils.utils import *

dict_of_dataset = dict
dict_of_win_list = dict


class ExperimentRunner:
    """
    Abstract class responsible for feature generators
    """
    METRICS_NAME = ['f1', 'roc_auc', 'accuracy', 'logloss', 'precision']

    def __init__(self, feature_generator_dict: dict = None,
                 boost_mode: bool = True,
                 static_booster: bool = False):
        """
        Constructor of class
        :param feature_generator_dict: dict that consists of 'generator_name': generator_class pairs
        :param boost_mode: defines whether to use error correction model or not
        :param static_booster: defines whether to use static booster or dynamic
        """
        self.feature_generator_dict = feature_generator_dict
        self.count = 0
        self.window_length = None
        self.logger = Logger().get_logger()
        self.boost_mode = boost_mode

        self.static_booster = static_booster
        self.y_test = None

    def generate_features_from_ts(self, ts_frame: pd.DataFrame,
                                  window_length: int = None) -> pd.DataFrame:
        """  Method responsible for generation of features from time series
        :return: dataframe with generated features
        """
        pass

    def extract_features(self, ts_data: pd.DataFrame, dataset_name: str = None):
        """
        Method responsible for extracting features from time series dataframe
        :param ts_data: dataframe with time series data
        :param dataset_name:
        :return:
        """
        pass

    @staticmethod
    def check_for_nan(ts: pd.DataFrame) -> pd.DataFrame:
        """
        Method responsible for checking if there are any NaN values in the time series dataframe
        and replacing them with 0
        :param ts: dataframe with time series data
        :return: dataframe with time series data without NaN values
        """
        if any(np.isnan(ts)):
            ts = np.nan_to_num(ts, nan=0)
        return ts

    @exception_decorator(exception_return=0.5)
    def get_roc_auc_score(self, pipeline, prediction, test_data):
        metric_roc = ROCAUC()
        try:
            score_roc_auc = metric_roc.metric(target=prediction.target, prediction=prediction.predict)
        except Exception:
            prediction = pipeline.predict(input_data=test_data, output_mode='probs')
            score_roc_auc = metric_roc.metric(target=prediction.target, prediction=prediction.predict)
        return score_roc_auc
