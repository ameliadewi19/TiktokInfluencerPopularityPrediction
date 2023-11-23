import json
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Function for linear regression
def linear_regression(X, y):
    model = LinearRegression()
    model.fit(X, y)
    return model

# Function to predict variabel for a given date
def predict(model, date_retrieve):
    X_pred = np.array([[date_retrieve]])
    return model.predict(X_pred)

# Function to perform linear regression for a specific username with the last 7 "statistic" data
def perform_linear_regression(data, variable_name):
    if not data:
        print("Empty data array provided.")
        return None

    # Select the last 7 "statistic" data
    last_7_statistic = data[-7:]

    # Prepare data for linear regression
    X = np.array([[datetime.strptime(data_point["dateRetrieve"], "%Y-%m-%d").timestamp()] for data_point in last_7_statistic])
    y = np.array([data_point[variable_name] for data_point in last_7_statistic])

    # Perform linear regression
    model = linear_regression(X, y)

    # Predict for the date after the last data
    last_data_date = datetime.strptime(last_7_statistic[-1]["dateRetrieve"], "%Y-%m-%d")
    date_to_predict = (last_data_date + timedelta(days=1)).strftime("%d-%m-%Y")
    timestamp_to_predict = datetime.strptime(date_to_predict, "%d-%m-%Y").timestamp()
    predicted = predict(model, timestamp_to_predict)

    # Return the result
    return {
        predicted[0]
    }