# prediction/sales_forecasting.py
from predictions import Prediction 
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd 


class SalesForecasting(Prediction):
    def forecast_monthly_sales(self):
        """Predict future sales using a linear regression model."""
        # Example: Simplified forecasting logic
        self.data['month_numeric'] = pd.to_datetime(self.data['month of sale'], errors='coerce').dt.month
        model = LinearRegression()
        x = np.array(self.data['month_numeric']).reshape(-1, 1)
        y = np.array(self.data['price']).reshape(-1, 1)
        model.fit(x, y)
        return model.predict([[12]])  # Example: Predict sales for December
