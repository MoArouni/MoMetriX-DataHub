import pandas as pd
from main import percentage 

class SalesAnalysis:
    def __init__(self, data):
        self.data = data
        self.collections = {
            "Handmade / Beaded": ["beaded anklets", "beaded bracelets", "beaded necklaces", "Earing Charms", "Key Chains", "BookMarks", "SET"],
            "Sterling Silver": ["Sterling Silver anklets", "Sterling Silver Bangles", "Sterling Silver Bracelets", 
                                "Sterling Silver Dangle Earrings", "Sterling Silver Necklaces", "Sterling Silver Nose rings", 
                                "Sterling Silver Rings", "Sterling Silver Stud Earings", "SET"],
            "Gold Plated": ["bangles", "cufflinks", "bracelets", "dangling earings", "stud earings", "rings", "necklaces", "SET"]
        }

    def calculate_pivot(data, months):
        """Generate the main pivot table from the given data."""
        pivot = pd.pivot_table(
            data,
            index="Product type",  # Or another appropriate column
            columns="Month of the year",  # Correct column name for month
            values="Price (per item unless its a set)",
            aggfunc="sum",
            fill_value=0
        )
        # Ensure the months are in the correct order
        return pivot.reindex(columns=months, fill_value=0)

    def add_totals(pivot):
        """Add row totals and column totals to the pivot table."""
        # Add row totals (sales for each product across all months)
        pivot["Product Total"] = pivot.sum(axis=1)

        # Add column totals (sales for each month across all products)
        month_totals = pivot.sum(axis=0)
        month_totals.name = "Month Total"

        # Concatenate the column totals as a new row at the bottom of the DataFrame
        pivot = pd.concat([pivot, month_totals.to_frame().T])
        
        return pivot, month_totals

    def swap_rows_and_columns(pivot):
        """Swap the last two rows and the last two columns of the pivot table."""
        # Swap the last two rows (Product Total and Percentage Month/Total)
        rows = pd.concat([pivot.iloc[:-2], pivot.iloc[-1:], pivot.iloc[-2:-1]])

        # Swap the last two columns (Product Total and Percentage Product/Total)
        return rows[[col for col in pivot.columns if col != "Product Total"] + ["Product Total", "Percentage Product/Total"]]



    def filter_day_range(self, start_date, end_date):
        """
        Filter the database for the given date range.
        """
        # Convert 'Day of the sale' from dd/mm/yy string format to datetime
        self.data['Day of the sale'] = pd.to_datetime(self.data['Day of the sale'], format='%m/%d/%Y')
        
        # Convert input start and end dates from dd/mm/yy to datetime
        start_date = pd.to_datetime(start_date, format='%m/%d/%Y')
        end_date = pd.to_datetime(end_date, format='%m/%d/%Y')

        # Filter the data based on the date range
        return self.data[(self.data['Day of the sale'] >= start_date) & (self.data['Day of the sale'] <= end_date)]
    
    def table_collection(self, product_type, filtered_data):
        """
        Generate a table for a specific product type's collections.
        Rows: Days in the interval.
        Columns: Collections for the product type (including an 'Other' column, which is assumed to already exist).
        """
        # Add a column on the far right for the total sales per day
    

        collections = self.collections.get(product_type, [])
        table = pd.DataFrame(index=filtered_data['Day of the sale'].dt.date.unique(), columns=collections + ['Other']).fillna(0)

        for _, row in filtered_data.iterrows():
            value = row[product_type + " collections"]
            price = row['Price (per item unless its a set)']

            # Check if the value belongs to the correct product type's column
            if pd.notna(value) and value in collections:
                table.loc[row['Day of the sale'].date(), value] += price
            elif pd.notna(value):
                # If the value is non-null and does not match any collection, add it to 'Other'
                table.loc[row['Day of the sale'].date(), 'Other'] += price

        # Add Totals row and column
        table['Day Total'] = table.sum(axis=1)  # Total for each day
        total_row = table.sum(axis=0)
        total_row.name = 'Total'
        table = pd.concat([table, total_row.to_frame().T])  # Add totals row

        return table

    def generate_db(self, filtered_data):
        """
        Generate the full database table for the date range.
        Add a totals row at the bottom and a totals column on the right.
        Ensure any missing columns or values are handled gracefully.
        """
        # Ensure 'Card amount paid' and 'Cash amount paid' exist
        payment_columns = ['Card amount paid', 'Cash amount paid']
        for column in payment_columns:
            if column not in filtered_data.columns:
                filtered_data[column] = 0  # Add missing columns with default value 0

        # Drop 'Timestamp' column if it exists
        if 'Timestamp' in filtered_data.columns:
            filtered_data = filtered_data.drop(columns=['Timestamp'])

        # Calculate the 'Total' column by summing 'Card amount paid' and 'Cash amount paid'
        filtered_data['Total'] = filtered_data[payment_columns].sum(axis=1)

        # Fill missing values with 0 for other columns
        filtered_data = filtered_data.fillna(0)

        # Create an empty totals row with the same columns as the DataFrame
        totals_row = pd.Series({col: "" for col in filtered_data.columns}, name=len(filtered_data))
        
        # Set the bottom-right cell ('Total') with the sum of the 'Total' column
        totals_row['Total'] = filtered_data['Total'].sum()

        # Append the totals row to the DataFrame
        final_table = pd.concat([filtered_data, totals_row.to_frame().T], ignore_index=True)

        return final_table



    def self_search(self, start_date, end_date):
        """
        Generate all Self Search tables for the given date range.
        """
        # Filter the data for the date range
        filtered_data = self.filter_day_range(start_date, end_date)

        # Generate tables for each product type
        handmade_table = self.table_collection("Handmade / beaded", filtered_data)
        sterling_silver_table = self.table_collection("Sterling Silver", filtered_data)
        gold_plated_table = self.table_collection("Gold Plated", filtered_data)

        # Generate the full database table
        full_database_table = self.generate_db(filtered_data)

        return {
            "Handmade / beaded": handmade_table,
            "Sterling Silver": sterling_silver_table,
            "Gold Plated": gold_plated_table,
            "Full Database": full_database_table
        }

    def get_average_sales(self):
        """Get average price per sale."""
        return self.data['Price (per item unless its a set)'].mean()
    
    def table_month(self):
        """
        Create a customized sales table with product types as rows,
        months as columns.
        """
        # Strip any spaces from column names (in case there are hidden spaces)
        self.data.columns = self.data.columns.str.strip()

        # Define the correct order of months
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        # Pivot the data to create a table with products as rows and months as columns
        pivot = pd.pivot_table(
            self.data,
            index="Product type",
            columns="Month of the year",
            values="Price (per item unless its a set)",
            aggfunc="sum",
            fill_value=0,
        )

        # Ensure the months are in the correct order
        pivot = pivot.reindex(columns=months, fill_value=0)

        # Add row totals (sales for each product across all months)
        pivot["Product Total"] = pivot.sum(axis=1)

        # Add column totals (sales for each month across all products)
        month_totals = pivot.sum(axis=0)
        month_totals.name = "Month Total"

        # Concatenate the column totals as a new row at the bottom of the DataFrame
        pivot = pd.concat([pivot, month_totals.to_frame().T])

        return pivot



    def table_week(self):
        """
        Create a customized sales table with product types as rows,
        months as columns, and row/column totals including a grand total.
        """
        # Define the correct order of months
        self.data.columns = self.data.columns.str.strip()
        
        week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # Pivot the data to create a table with products as rows and months as columns
        pivot = pd.pivot_table(
            self.data,
            index="Product type",
            columns="Day of the week",
            values="Price (per item unless its a set)",
            aggfunc="sum",
            fill_value=0,
        )

        # Ensure the months are in the correct order
        pivot = pivot.reindex(columns=week, fill_value=0)

        # Add row totals (sales for each product across all months)
        pivot["Product Total"] = pivot.sum(axis=1)

        # Add column totals (sales for each month across all products)
        week_totals = pivot.sum(axis=0)
        week_totals.name = "Week Total"

        # Concatenate the column totals as a new row at the bottom of the DataFrame
        pivot = pd.concat([pivot, week_totals.to_frame().T])

        return pivot

    def table_payment(self):
        """
        Create a sales table with product types as rows, payment types (Card and Cash) as columns,
        and row/column totals including a grand total.
        Add a 'Price Check' column to validate Price = Card Paid + Cash Paid.
        """
        # Strip any spaces from column names
        self.data.columns = self.data.columns.str.strip()

        # Define the payment-related columns
        payment_columns = ["Card amount paid", "Cash amount paid"]

        # Add missing columns with NaN instead of 0
        for column in payment_columns:
            if column not in self.data.columns:
                self.data[column] = None  # Add missing columns with NaN

        # Fill only the payment columns where values are NaN with 0
        self.data[payment_columns] = self.data[payment_columns].fillna(0)

        # Ensure 'Price' column exists

        # Pivot the data to create a table with products as rows and payment types as columns
        pivot = pd.pivot_table(
            self.data,
            index="Product type",  # Rows for product types
            values=payment_columns,
            aggfunc="sum",  # Sum values for each column
            fill_value=0  # Fill missing values with 0
        )

        # Add a Product Total column to sum Card and Cash for each product type
        pivot["Product Total"] = pivot["Card amount paid"] + pivot["Cash amount paid"]

        # Calculate totals for each payment type, Price, and Product Total
        payment_totals = pivot.sum(axis=0)
        payment_totals.name = "Total"

        # Add the totals as a new row at the bottom of the DataFrame
        pivot = pd.concat([pivot, payment_totals.to_frame().T])

        return pivot
