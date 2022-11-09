import os
import shutil
import urllib.request as request
import zipfile

import numpy as np
import pandas as pd
from scipy.io.arff import loadarff

from core.operation.utils.LoggerSingleton import Logger
from core.operation.utils.utils import PROJECT_PATH


class DataLoader:
    """Class for reading data from tsv files and downloading from UCR archive if not found.

    Args:
        dataset_name (str): name of dataset

    Examples:
        >>> data_loader = DataLoader('ItalyPowerDemand')
        >>> train_data, test_data = data_loader.load_data()
    """

    def __init__(self, dataset_name: str):
        self.logger = Logger().get_logger()
        self.dataset_name = dataset_name

    def load_data(self) -> tuple:
        """Load data for classification experiment locally or externally from UCR archive.

        Returns:
            tuple: train and test data
        """
        dataset_name = self.dataset_name
        self.logger.info(f'Reading {dataset_name} data locally')
        train_data, test_data = self.read_tsv(dataset_name)

        if train_data is None:
            self.logger.info(f'Dataset {dataset_name} not found in data folder. Downloading...')

            # Create temporary folder for downloaded data
            cache_path = os.path.join(PROJECT_PATH, 'temp_cache/')
            download_path = cache_path + 'downloads/'
            temp_data_path = cache_path + 'temp_data/'
            filename = 'temp_data_{}'.format(dataset_name)
            for _ in (download_path, temp_data_path):
                os.makedirs(_, exist_ok=True)

            url = f"http://www.timeseriesclassification.com/Downloads/{dataset_name}.zip"
            request.urlretrieve(url, download_path + filename)
            try:
                zipfile.ZipFile(download_path + filename).extractall(temp_data_path)
            except zipfile.BadZipFile:
                self.logger.error(f'Cannot extract data: {dataset_name} dataset not found in UCR archive')
                return None, None

            self.logger.info(f'{dataset_name} data downloaded. Unpacking...')
            train_data, test_data = self.extract_data(dataset_name, temp_data_path)

            shutil.rmtree(cache_path)
            return train_data, test_data

        return train_data, test_data

    def extract_data(self, dataset_name: str, temp_data_path: str):
        """Unpacks data from downloaded file and saves it into Data folder with .tsv extension.

        Args:
            dataset_name (str): name of dataset
            temp_data_path (str): path to temporary folder with downloaded data

        Returns:
            tuple: train and test data

        """

        # If data unpacked as .txt file
        if os.path.isfile(temp_data_path + '/' + dataset_name + '_TRAIN.txt'):
            x_test, x_train, y_test, y_train = self.read_txt(dataset_name, temp_data_path)

        # If data unpacked as .arff file
        elif os.path.isfile(temp_data_path + '/' + dataset_name + '_TRAIN.arff'):
            x_test, x_train, y_test, y_train = self.read_arff(dataset_name, temp_data_path)

        else:
            self.logger.error('Data unpacking error')
            return None, None

        # Conversion of target values to int or str
        try:
            y_train = y_train.astype('float64').astype('int64')
            y_test = y_test.astype('float64').astype('int64')
        except ValueError:
            y_train = y_train.astype(str)
            y_test = y_test.astype(str)

        # Save data to tsv files
        data_path = os.path.join(PROJECT_PATH, 'data', dataset_name)
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        self.logger.info(f'Saving {dataset_name} data to tsv files')
        for subset in ('TRAIN', 'TEST'):
            df = pd.DataFrame(x_train if subset == 'TRAIN' else x_test)
            df.insert(0, 'class', y_train if subset == 'TRAIN' else y_test)
            df.to_csv(os.path.join(data_path, f'{dataset_name}_{subset}.tsv'), sep='\t', index=False, header=False)

        del df
        return (pd.DataFrame(x_train), y_train), (pd.DataFrame(x_test), y_test)

    def read_arff(self, dataset_name, temp_data_path):
        """Reads data from .arff file.

        """
        train = loadarff(temp_data_path + dataset_name + '_TRAIN.arff')
        test = loadarff(temp_data_path + dataset_name + '_TEST.arff')
        try:
            data_train = np.asarray([train[0][name] for name in train[1].names()])
            x_train = data_train[:-1].T.astype('float64')
            y_train = data_train[-1]

            data_test = np.asarray([test[0][name] for name in test[1].names()])
            x_test = data_test[:-1].T.astype('float64')
            y_test = data_test[-1]
        except Exception:
            x_train, y_train = self.load_re_arff(temp_data_path + dataset_name + '_TRAIN.arff')
            x_test, y_test = self.load_re_arff(temp_data_path + dataset_name + '_TEST.arff')
        return x_test, x_train, y_test, y_train

    @staticmethod
    def read_txt(dataset_name, temp_data_path):
        """
        Reads data from .txt file.
        Args:
            dataset_name (str): name of dataset
            temp_data_path (str): path to temporary folder with downloaded data

        Returns:
            tuple: train and test data
        """
        data_train = np.genfromtxt(temp_data_path + '/' + dataset_name + '_TRAIN.txt')
        data_test = np.genfromtxt(temp_data_path + '/' + dataset_name + '_TEST.txt')
        x_train, y_train = data_train[:, 1:], data_train[:, 0]
        x_test, y_test = data_test[:, 1:], data_test[:, 0]
        return x_test, x_train, y_test, y_train

    @staticmethod
    def read_tsv(file_name: str):
        """Read tsv file that contains data for classification experiment. Data must be placed
        in 'data' folder with .tsv extension.

        Args:
            file_name (str): name of file with data

        Returns:
            tuple: (x_train, x_test) and (y_train, y_test)

        """
        try:
            df_train = pd.read_csv(os.path.join(PROJECT_PATH, 'data', file_name, f'{file_name}_TRAIN.tsv'),
                                   sep='\t',
                                   header=None)

            x_train = df_train.iloc[:, 1:]
            y_train = df_train[0].values

            df_test = pd.read_csv(os.path.join(PROJECT_PATH, 'data', file_name, f'{file_name}_TEST.tsv'),
                                  sep='\t',
                                  header=None)

            x_test = df_test.iloc[:, 1:]
            y_test = df_test[0].values
            y_train, y_test = y_train.astype(int), y_test.astype(int)

            return (x_train, y_train), (x_test, y_test)
        except FileNotFoundError:
            return None, None

    @staticmethod
    def load_re_arff(data):
        """
        Reads data from relational .arff file.
        Args:
            data: ...

        Returns:

        """
        x_data = np.asarray(data[0])
        n_samples = len(x_data)
        x_ls, y_ls = [], []

        if x_data[0][0].dtype.names is None:
            for i in range(n_samples):
                x_sample = np.asarray([x_data[i][name] for name in x_data[i].dtype.names])
                x_ls.append(x_sample.T)
                y_ls.append(x_data[i][1])
        else:
            for i in range(n_samples):
                x_sample = np.asarray([x_data[i][0][name] for name in x_data[i][0].dtype.names])
                x_ls.append(x_sample.T)
                y_ls.append(x_data[i][1])

        x_arr = np.asarray(x_ls).astype('float64')
        y_arr = np.asarray(y_ls)

        try:
            y_arr = y_arr.astype('float64').astype('int64')
        except ValueError:
            y_arr = y_arr.astype(str)

        return x_arr, y_arr


# Example of usage
if __name__ == '__main__':
    ds_name = [
        'DodgerLoopDay',
        'Beef',
        'Coffee',
        'SonyAIBORobotSurface1',
        'SonyAIBORobotSurface122',  # fake dataset
        'Lightning7',
        'UMD',
    ]

    for ds in ds_name:
        loader = DataLoader(ds)
        train, test = loader.load_data()
        if train:
            print(f'{ds} train_X: {train[0].shape}, test_X: {test[0].shape}')
            print(f'{ds} train_y: {train[1].shape}, test_y: {test[1].shape}')
        else:
            continue
