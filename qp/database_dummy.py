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
from influxdb import DataFrameClient
import pandas as pd
import os
import datetime


class NoDataError(Exception):
    pass


class DATABASE(object):

    def __init__(self, dbname, user='root', password='root', host='r4-influxdb.ricplt', port='8086'):
        self.client = DataFrameClient(host, port, user, password, dbname)
        self.data = None

    def read_data(self, meas='ueMeasReport', limit=100000, cellid=False, ueid=False):
        query = """select * from """ + meas

        if cellid:
            query += " where nrCellIdentity= '" + cellid + "'"

        if ueid:
            query += """ where "ue-id"  = \'{}\'""".format(ueid)
        query += "  ORDER BY DESC LIMIT " + str(limit)
        result = self.client.query(query)
        try:
            if len(result) != 0:
                # print("Querying data : " + meas + " : size - " + str(len(result[meas])))
                self.data = result[meas]
                self.data['measTimeStampRf'] = self.data.index
            else:
                raise NoDataError

        except NoDataError:
            if cellid:
                print('Data not found for ' + meas + ' CellID : '+cellid)
            elif ueid:
                print('Data not found for ' + meas + ' UEID : '+ueid)
            else:
                print('Data not found for ' + meas)
            pass

    def write_prediction(self, df, meas_name='QP'):
        df.index = pd.date_range(start=datetime.datetime.now(), freq='10ms', periods=len(df))
        self.client.write_points(df, meas_name)


class DUMMY:

    def __init__(self):
        self.ueid = pd.DataFrame([[1001, "Car-2", pd.to_datetime("2021-06-25T11:42:58.855"), "Throughput RSRP"]], columns=["du-id", "ue-id", "measTimeStampRf", "Degradation"])
        self.ue = pd.read_csv('valid.csv')
        #self.ue = self.ue[self.ue['ue-id'] == ueid]
        
        #Split Train / Test sets    75/25
        test_size = int(0.25*len(self.ue))
        self.train = self.ue[:-test_size]
        self.test = self.ue[-test_size:]
        self.test = self.test[self.test['ue-id'] == self.ueid["ue-id"][0]]
        self.data = None

    def read_data(self, meas='ueMeasReport', limit=100000, cellid=False, cell=False, ueid=False):
        
        if meas == 'train':
            self.data = self.train.head(limit)
            if cellid:
                self.data = self.data[self.data['ue-id'] == self.ueid["ue-id"][0]]
                if cell == 0:  # Serving cell
                    self.data = self.data[self.data['nrCellIdentity'] == cellid]
                else: # Neighbor cells
                    self.data = self.data[self.data[f"nbCellIdentity_{cell-1}"] == cellid]
                
            
        if meas == 'liveUE':   
            if ueid:
                self.data = self.test[self.test['ue-id'] == ueid]
                self.data = self.data.head(limit)
            if cellid:
                if cell==0: # Serving cell
                    self.data = self.test[self.test['nrCellIdentity'] == cellid]
                    self.data = self.data.head(limit)
                else:     # neighbors
                    self.data= self.test[self.test[f"nbCellIdentity_{cell-1}"] == cellid]
                    self.data = self.data.head(limit)
 

    def write_prediction(self, df, meas_name='QP'):
        if os.path.isfile('qp_results.csv'):
            df.to_csv('qp_results.csv', header=None, mode="a")
        else:
            df.to_csv('qp_results.csv')
