from typing import Union

import numpy as np
import pandas as pd
import pywt

from core.models.statistical.stat_features_extractor import StatFeaturesExtractor


class WaveletExtractor:
    """Decomposes the given time series with a singular-spectrum analysis. Assumes the values of the time series are
    recorded at equal intervals.

    Args:
        time_series: The time series to be decomposed.
        wavelet_name: The name of the wavelet to be used for decomposition.

    Attributes:
        discrete_wavelets: List of discrete wavelets.
        continuous_wavelets: List of continuous wavelets.

    """

    def __init__(self,
                 time_series: Union[pd.DataFrame, pd.Series, np.ndarray, list],
                 wavelet_name: str = None):
        self.time_series = time_series
        self.discrete_wavelets = pywt.wavelist(kind='discrete')
        self.continuous_wavelets = pywt.wavelist(kind='continuous')
        self.wavelet_name = wavelet_name

    @property
    def decomposing_level(self):
        """The level of decomposition of the time series.

        Returns:
            The level of decomposition of the time series.
        """
        return pywt.dwt_max_level(len(self.time_series), self.wavelet_name)

    def decompose_signal(self, ts=None):
        if ts is None:
            ts = self.time_series
        if self.wavelet_name in self.discrete_wavelets:
            return pywt.dwt(ts,
                            self.wavelet_name,
                            'smooth')
        else:
            return pywt.cwt(ts,
                            self.wavelet_name)

    def generate_features_from_AC(self,
                                  HF,
                                  LF,
                                  level: int = 3):
        extractor = StatFeaturesExtractor()
        feature_list = []
        feature_df = extractor.create_features(LF)
        feature_df.columns = [f'{x}_LF' for x in feature_df.columns]
        feature_list.append(feature_df)
        for i in range(self.decomposing_level):
            feature_df = extractor.create_features(HF)
            feature_df.columns = [f'{x}_level_{i}' for x in feature_df.columns]
            feature_list.append(feature_df)
            HF = self.decompose_signal(ts=HF)[0]
        return feature_list

    @staticmethod
    def detect_peaks(x: np.ndarray,
                     mph: int = None,
                     mpd: int = 1,
                     threshold: int = 0,
                     edge: str = 'rising',
                     kpsh: bool =False,
                     valley: bool = False) -> np.ndarray:
        """Detect peaks in data based on their amplitude and other features.

        Args:
            x: data.
            mph: detect peaks that are greater than minimum peak height (if parameter `valley` is
                False) or peaks that are smaller than maximum peak height (if parameter `valley` is True).
            mpd: detect peaks that are at least separated by minimum peak distance (in number
                of data points).
            threshold: detect peaks (valleys) that are greater (smaller) than `threshold`
                in relation to their immediate neighbors.
            edge: for a flat peak, keep only the rising edge ('rising'), only the falling edge
                ('falling'), both edges ('both'), or don't detect a flat peak (None).
            kpsh: keep peaks with same height even if they are closer than `mpd`.
            valley: if True (1), detect valleys (local minima) instead of peaks.

        Returns:
            Indices of the peaks in `x`.

        """

        x = np.atleast_1d(x).astype('float64')
        if x.size < 3:
            return np.array([], dtype=int)
        if valley:
            x = -x
        # find indices of all peaks
        dx = x[1:] - x[:-1]
        # handle NaN's
        indnan = np.where(np.isnan(x))[0]
        if indnan.size:
            x[indnan] = np.inf
            dx[np.where(np.isnan(dx))[0]] = np.inf
        ine, ire, ife = np.array([[], [], []], dtype=int)
        if not edge:
            ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
        else:
            if edge.lower() in ['rising', 'both']:
                ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
            if edge.lower() in ['falling', 'both']:
                ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
        ind = np.unique(np.hstack((ine, ire, ife)))
        # handle NaN's
        if ind.size and indnan.size:
            # NaN's and values close to NaN's cannot be peaks
            ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan - 1, indnan + 1))), invert=True)]
        # first and last values of x cannot be peaks
        if ind.size and ind[0] == 0:
            ind = ind[1:]
        if ind.size and ind[-1] == x.size - 1:
            ind = ind[:-1]
        # remove peaks < minimum peak height
        if ind.size and mph is not None:
            ind = ind[x[ind] >= mph]
        # remove peaks - neighbors < threshold
        if ind.size and threshold > 0:
            dx = np.min(np.vstack([x[ind] - x[ind - 1], x[ind] - x[ind + 1]]), axis=0)
            ind = np.delete(ind, np.where(dx < threshold)[0])
        # detect small peaks closer than minimum peak distance
        if ind.size and mpd > 1:
            ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
            idel = np.zeros(ind.size, dtype=bool)
            for i in range(ind.size):
                if not idel[i]:
                    # keep peaks with the same height if kpsh is True
                    idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) \
                           & (x[ind[i]] > x[ind] if kpsh else True)
                    idel[i] = 0  # Keep current peak
            # remove the small peaks and sort back the indices by their occurrence
            ind = np.sort(ind[~idel])

        return ind
