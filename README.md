# qp-xapp-dummy
Mirror of the ric-app/qp repo for Dummy evaluation (modified codes according to E release)

NEW FILES / MODIFICATIONS

main_dummy.py:
* start(): Populate DB – Use DUMMY (‘qp/valid.csv’)
* If Model is not present in the current path, run train() to train the model for the prediction.



# ==================================================================================
Original E release branch - Predicts pdcpBytes only for a nb cell 'c2/B13' with VAR model.

database.py:   DUMMY 
  *  Anomalous UE input ("liveUE") : 'Waiting passenger 9' with nb CellID 'c2/B13'
  *  Cell data ("liveCell"):  Reads 'dummy.csv' for 'c2/B13' data.

main.py:
 a. start(): Populate DB –  DUMMY (‘qp/dummy.csv’)
 b. qp_predict_handler() -  pred_msg = predict(summary[])
 c. predict(payload) : Function that forecast the time series
	1. from payload -> ueid
	2. Extract neighbors cell id -> cell_list = cells(ueid)
	3. Loop in cell_list: Read data for each cell id 
      4. inp = Read 11 time series from “liveCell”  (dummy.csv)
      5. train(data,cid) -> VAR model for each nb cell
      6. Forecast the time series (inp) using the saved model -> forecast(inp,mcid,1)


qptrain.py :  train(db,cid)
  1. Read the input file(based on cell id received from the main program) – read 'dummy.csv'
  2. Call process() to forecast the downlink and uplink (pdcpBytes) of the input cell id ('C2/B13').
  3. make_stationary() -> Check for Stationarity and make the Time Series Stationary 
      a. Perform ADF (ADFuller) test to check stationarity  -> adfuller_test(column) 
      b. If the columns is stationary, perform 1st differencing and return data.
  4. Make a VAR (Vector Autoregression) model.
  5. Call the fit method with the desired lag order 10.
  6. Save model with the cell id name.
  
 
prediction.py:  Forecast the (past) time series (from "liveCell") using saved model.
  1. Make stationary.
  2. pred = var_model(mcid).forecast
  
  
insert.py: This module is temporary which aims to populate cell data (from Viavi) into influxDB.
This will be depreciated once KPIMON push cell info into influxDB.


