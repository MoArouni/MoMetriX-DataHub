import pandas as pd

def get_latest_date(file_path):
    """
    Reads the last row of the CSV file and extracts the latest date of sale.
    
    Args:
        file_path (str): Path to the CSV file.

    Returns:
        str: Latest date of sale in 'YYYY-MM-DD' format.
    """
    try:
        # Load only the last row of the CSV
        data = pd.read_csv(file_path)
        last_row = data.iloc[-1]  # Get the last row
        latest_date = f"{last_row['Day of the sale ? ']}"
        return latest_date
    except Exception as e:
        return f"An error occurred: {e}"

csv_path = "data/sample_data.csv"  # Adjust this path as needed
latest_date = get_latest_date(csv_path)
print(f"The latest date of sale in the database is: {latest_date}")









