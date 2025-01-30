import pandas as pd 

def get_latest_date(file_path):
    """Returns the latest date from the CSV file."""
    try:
        data = pd.read_csv(file_path)
        last_row = data.iloc[-1]
        latest_date = f"{last_row['Day of the sale']}"

        return latest_date
    except Exception as e:
        return f"An error occurred: {e}"
    
def get_amount_rows(file_path):
    """Returns the amount of lines in the CSV file."""
    try:
        data = pd.read_csv(file_path)
        return len(data)
    except Exception as e:
        return f"An error occurred: {e}"
        
def load_data():
    """Loads the CSV data."""
    try:
        data = pd.read_csv("data/sales.csv")  # Replace with the correct path
        return data
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None



def percentage(sub_total, total):
    """
    Calculate percentage of sub_total compared to total.
    """
    if total == 0:  # Avoid division by zero
        return 0
    return round((sub_total / total) * 100)



def format_percentage(values):
    """Format the given values as percentages with two decimal places."""
    return values.apply(lambda x: f"{x:.2f}%")

