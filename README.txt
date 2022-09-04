# qp-xapp-dummy
Mirror of the ric-app/qp repo for Dummy evaluation (modified codes according to E release)
Uses only UE data instead of Cell data. Predicts 'throughput' instead of 'pdcpBytes'.

NEW FILES / MODIFICATIONS
To obtain throughput values for neighboring cells -> Random Forest Regressor (RF) predictor (explained in 'tp_model/tptrain.ipynb')
To predict throughput -> VAR (or ARIMA) time series ML predictor
Interpolation added before VAR to get regular time series (sample ever 10ms)


database_dummy.py:
	* An anomalous UEID is specified as the input (sent from TS) for the prediction. Default: "Car-2"
	* Dataset is 'valid.csv' split into train ("train") and test ("liveUE")
	* Test data is filtered by the ueid.
	* write_prediction(df): dump prediction results into a .csv
	
	

main_dummy.py:
* start(): Populate DB – Use DUMMY (‘qp/valid.csv’)
	* If 'RF' is not present in the current path, run tp_train() to train the model that obtains throughput for nb cells.
	* Obtain anomalous UEID input from database --> pred_msg = predict(ue)
* predict(payload) : Function that forecast the time series
	1. from payload -> ueid
	2. Extract neighbors cell id -> cell_list = cells(ueid)
	3. Loop in cell_list: Read data for each cell id (cid)
	      4. inp = Read 11 samples of cellid from “liveUE” 
	      5. train(data,cid,i) -> VAR model generated for each cid
	      6. Forecast the time series (inp) using the saved model for the next nobs samples -> forecast(inp,mcid,nobs)
	      7. Validation of the predictions with RMSE error.
	      
	
	
qptrain_VAR.py - train(db,cid,i)
  1. Reads "train" historical data of the cid (in ueid)
  2. Call process() to filter 'throughput' and 'measTimeStampRF' + 10 ms data interpolation.
  	* For nb cells (i != 0) --> tp_predict (df,i) : apply 'RF' model to obtain throughput column as 'tput_nbi'
  3. make_stationary() -> Check for Stationarity and make the Time Series Stationary 
      a. Perform ADF (ADFuller) test to check stationarity  -> adfuller_test(column) 
      b. If the columns is stationary, perform 1st differencing and return data.
  4. Make a VAR (Vector Autoregression) model.
  5. Call the fit method with the desired lag order 10.
  6. Save model with the cell id name.


prediction.py - forecast(inp, mcid, i, nobs): Forecast the (past) time series (from "liveUE") using saved model.
nobs is the number of observations that want to get predicted in the future (every 10 ms)
Default: nobs = 5
  1. Call process() to filter columns, obtain troughput for nb cells and apply data interpolation.
  2. Make stationary.
  3. pred = var_model.forecast(data,nobs)
  4. Set index timestamp for the predictions.

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


