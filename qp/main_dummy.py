# ==================================================================================
#       Copyright (c) 2020 AT&T Intellectual Property.
#       Copyright (c) 2020 HCL Technologies Limited.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ==================================================================================
"""
qp module main -- using Time series ML predictor

RMR Messages:
 #define TS_UE_LIST 30000
 #define TS_QOE_PREDICTION 30002
30000 is the message type QP receives from the TS;
sends out type 30002 which should be routed to TS.

"""
import insert
import os
import json
#from mdclogpy import Logger
#from ricxappframe.xapp_frame import RMRXapp, rmr
from prediction import forecast
from qptrain import train, PROCESS
from database_dummy import DATABASE, DUMMY
from tp_model.tp_train import tp_train
from tp_model.tp_predict import tp_predict
from sklearn.metrics import mean_squared_error
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# pylint: disable=invalid-name
qp_xapp = None
#logger = Logger(name=__name__)


def cells(ue):
    """
        Extract neighbor cell id for a given UE
    """
    db = DUMMY()
    db.read_data(meas='liveUE', limit=1, ueid=ue)
    df = db.data

    nbc = df.filter(regex='nbCell').values[0].tolist()
    srvc = df.filter(regex='nrCell').values[0].tolist()
    return srvc+nbc


def predict(payload):
    """
     Function that forecast the time series
    """
    tp = {}
    ueid = payload["ue-id"][0]
    nobs = 3
    
    cell_list = cells(ueid)
    print(cell_list)
    
    '''
    db.read_data(meas='liveUE', cell=0, cellid=cid, limit=11)
    if len(db.data) != 0:
        #inp = tp_predict(db.data)  #adds throughput of nb cells
        inp = db.data
        inp.to_csv(ueid + ".csv", index=False)
    '''
    
    
    for i,cid in enumerate(cell_list):    #if i=0, is serving cell. Others nb_cell.
        mcid = cid.replace('/', '')
        print("-------CELL ", cid, "---------------")
        
        db.read_data(meas='liveUE', cell=i, cellid=cid, limit=11)
        if len(db.data) != 0:
            inp = db.data  #adds throughput of nb cells
            #inp.to_csv(ueid + ".csv", index=False)
        
            
            # VAR TRAINING - per cell - to learn its behavior
            print("----------- VAR TRAINING ----------")
            if not os.path.isfile('qp/' + mcid):
                train(db, cid, i)

            print("----------- VAR PREDICTION ----------")
            df_f = forecast(inp, mcid, i, nobs)
            print(df_f) 
            
             #VALIDATION
            time = df_f.index
            db.read_data(meas='liveUE', cell=i, cellid=cid)
            ps = PROCESS(db.data.copy())
            ps.process(i)
            labels = ps.data[ps.data.index.isin(time)]
            print("LABELS \n", labels)
            
            rmse = np.sqrt(mean_squared_error(labels*1000, df_f*1000))
            print('Test RMSE: %.3f' % rmse)
            
            
            if df_f is not None:
                tp[cid] = df_f.values.tolist()[0]
                df_f['cellid'] = cid
                db.write_prediction(df_f)
            else:
                tp[cid] = [None, None]
                
    print(json.dumps({ueid: tp}))
    return json.dumps({ueid: tp})


def start(thread=False):
    """
    This is a convenience function that allows this xapp to run in Docker
    for "real" (no thread, real SDL), but also easily modified for unit testing
    (e.g., use_fake_sdl). The defaults for this function are for the Dockerized xapp.
    """
    global qp_xapp
    global db
    if not thread:
        insert.populatedb()   # temporory method to popuate db, it will be removed when data will be coming through KPIMON to influxDB
        db = DATABASE('UEData')
    else:
        db = DUMMY()
    if not os.path.isfile('RF'):
        tp_train(db)
    
    file = 'qp_results.csv'
    if(os.path.exists(file) and os.path.isfile(file)):
          os.remove(file)
            
    ue = db.ueid 
    print(ue)
    
    pred_msg = predict(ue)
    
    
    
    #qp_xapp.register_callback(qp_predict_handler, 30000)
    #qp_xapp.run(thread)


def stop():
    """
    can only be called if thread=True when started
    TODO: could we register a signal handler for Docker SIGTERM that calls this?
    """
    global qp_xapp
    qp_xapp.stop()


def get_stats():
    """
    hacky for now, will evolve
    """
    global qp_xapp
    return {"PredictRequests": qp_xapp.predict_requests}

start(True)