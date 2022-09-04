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
# import pandas as pd
import os
import joblib
import pandas as pd
from qptrain import PROCESS


def forecast(data, cid, i, nobs=1):
    """
     forecast the time series using the saved model.
    """
    ps = PROCESS(data.copy())
    ps.process(i)
    data = ps.data.copy()
    
    ps.make_stationary()
    
    file_name = cid.replace('/', '')

    if not ps.valid():
        df_f = data.tail(3)
        df_f.index = pd.date_range(start=data.index[-1], freq='10ms', periods=len(df_f)+1, closed='right')
    elif os.path.isfile(file_name):
        model = joblib.load(file_name)
        pred = model.forecast(y=ps.data.values, steps=nobs)

        if pred is not None:
            df_f = pd.DataFrame(pred, columns=data.columns)
            df_f.index = pd.date_range(start=data.index[-1], freq='10ms', periods=len(df_f)+1, closed='right')
            df_f = df_f[data.columns]
            df_f = ps.invert_transformation(data, df_f)
    else:
        return None
    df_f = df_f[data.columns]
    return df_f
