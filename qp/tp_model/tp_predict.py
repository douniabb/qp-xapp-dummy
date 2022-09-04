import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from tp_model.processing import PREPROCESS
import joblib


def tp_predict(dataset,i=False):
    """

    """
    if i:
        nb = dataset[['prb_usage', f"rsrp_nb{i-1}", f"rsrq_nb{i-1}", f"rssinr_nb{i-1}"]]
        sc = joblib.load('scale')
        nb = sc.transform(nb)

        model = joblib.load('RF')
        throughput = model.predict(nb)
        dataset[f"tput_nb{i-1}"] = throughput
        return dataset
    
    else:
        for i in range(5):
            nb = dataset[['prb_usage', f"rsrp_nb{i}", f"rsrq_nb{i}", f"rssinr_nb{i}"]]
            sc = joblib.load('scale')
            nb = sc.transform(nb)

            model = joblib.load('RF')
            throughput = model.predict(nb)
            dataset[f"tput_nb{i}"] = throughput
        return dataset
        
        
