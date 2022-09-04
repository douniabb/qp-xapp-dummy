import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from tp_model.processing import PREPROCESS
import joblib


def tp_train(db):
    """
     Make a RF model.
     Creates an RF predictor model to predict throughput from signal strength metrics.
     Uses non anomalous data as input.
    """
    db.read_data(meas='train') 
    data = db.data.loc[db.data["Anomaly"]==0]
    ps = PREPROCESS(data)
    ps.process()
    df = ps.data
    
    x = df  # [prb_usage, rsrp, rsrq, rssinr]
    y = data[['throughput']]
    
    model = RandomForestRegressor(max_depth=9)
    model.fit(x, y.values.ravel())
    
    with open('RF', 'wb') as f:
        joblib.dump(model, f)     # Save the model 
    
   