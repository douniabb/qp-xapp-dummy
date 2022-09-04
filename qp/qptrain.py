# ==================================================================================
#  Copyright (c) 2020 HCL Technologies Limited.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ==================================================================================

from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller
from tp_model.tp_predict import tp_predict
import pandas as pd
import numpy as np
import traces
import os
import joblib


class DataNotMatchError(Exception):
    pass


class PROCESS(object):

    def __init__(self, data):
        self.diff = 0
        self.data = data
        
    def interpolate(self):
        """Interpolate time series to get regular samples"""
        df = self.data.copy()
        resample_index = pd.date_range(start=df.index[0], end=df.index[-1], freq='10ms')
        dummy_frame = pd.DataFrame(np.NaN, index=resample_index, columns=df.columns)  
        df = df.combine_first(dummy_frame).interpolate('time')
        df['tputUL'] = df['tput']
        self.data = df
        

    def adfuller_test(self, series, thresh=0.05, verbose=False):
        """ADFuller test for Stationarity of given series and return True or False"""
        r = adfuller(series, autolag='AIC')
        output = {'test_statistic': round(r[0], 4), 'pvalue': round(r[1], 4), 'n_lags': round(r[2], 4), 'n_obs': r[3]}
        p_value = output['pvalue']
        if p_value <= thresh:
            return True #stationary
        else:
            return False

    def make_stationary(self):
        """ call adfuller_test() to check for stationary
            If the column is stationary, perform 1st differencing and return data"""
        df = self.data.copy()
        res_adf = []
        for name, column in df.iteritems():
            res_adf.append(self.adfuller_test(column))  # Perform ADF test
        if not all(res_adf):
            self.data = df.diff().dropna()
            self.diff += 1

    def invert_transformation(self, inp, forecast):
        """Revert back the differencing to get the forecast to original scale."""
        if self.diff == 0:
            return forecast
        df = forecast.copy()
        columns = inp.columns
        for col in columns:
            df[col] = inp[col].iloc[-1] + df[col].cumsum()
        self.diff = 0
        return df

    def process(self,i):
        """ Filter throughput parameters, call make_stationary() to check for Stationarity time series
        """
        df = self.data.copy()
        df['measTimeStampRf'] = pd.to_datetime(df['measTimeStampRf'])  
        
        if i==0:
            df = df[['measTimeStampRf', 'throughput']]
            df = df.rename(columns={"throughput": "tput"})
            self.data = df.set_index('measTimeStampRf')
        else:
            df = tp_predict(df,i)
            df = df[['measTimeStampRf', f"tput_nb{i-1}"]]
            df = df.rename(columns={f"tput_nb{i-1}": "tput"})
            self.data = df.set_index('measTimeStampRf')

        #self.data['tputUL'] = self.data['tput']
        #self.data = df.loc[:, (df != 0).any(axis=0)]    
        self.interpolate()

    def valid(self):
        val = False
        if self.data is not None:
            df = self.data.copy()
            df = df.loc[:, (df != 0).any(axis=0)]
            if len(df) != 0 and df.shape[1] == 2:
                val = True
        return val


def train(db, cid, i):
    """
     Read the input file(based on cell id received from the main program)
     call process() to forecast the downlink and uplink of the input cell id
     Make a VAR model, call the fit method with the desired lag order.
    """
    db.read_data(meas='train', cellid=cid, cell=i)
    md = PROCESS(db.data)
    md.process(i)
    md.make_stationary()
    if md.valid():
        model = VAR(md.data)          # Make a VAR model
        model_fit = model.fit(10)            # call fit method with lag order
        file_name = cid.replace('/', '')
        with open(file_name, 'wb') as f:
            joblib.dump(model_fit, f)     # Save the model with the cell id name
