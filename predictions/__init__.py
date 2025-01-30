# predictions/__init__.py
import pandas as pd

class Prediction:
    def __init__(self, data: pd.DataFrame):
        self.data = data
