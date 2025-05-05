import csv
import pandas as pd
from typing import Dict, List, Any, Optional
import re
import json
import datetime

class CSVValidationError(Exception):
    """Exception raised for CSV validation errors"""
    pass

class CSVValidator:
    """
    Service for validating CSV files against schemas and inserting data.
    This class ensures that uploaded data conforms to the expected format.
    """
    
    def __init__(self, file_path: str, schema: Dict[str, Any], has_headers: bool = True):
        """
        Initialize the validator
        
        Args:
            file_path: Path to the CSV file
            schema: Schema dictionary defining the expected structure
            has_headers: Whether the CSV file has header row
        """
        self.file_path = file_path
        self.schema = schema
        self.has_headers = has_headers
        
    def validate(self) -> pd.DataFrame:
        """
        Validate the CSV file against the schema
        
        Returns:
            Pandas DataFrame of the validated data
        
        Raises:
            CSVValidationError: If validation fails
        """
        try:
            # Read CSV file
            data = pd.read_csv(self.file_path, header=0 if self.has_headers else None)
            
            # If schema is empty, just return the data
            if not self.schema or "fields" not in self.schema:
                return data
                
            # Get expected fields
            expected_fields = [field["name"] for field in self.schema["fields"]]
            
            # Check if columns match expected fields
            if self.has_headers:
                missing_fields = [field for field in expected_fields if field not in data.columns]
                if missing_fields:
                    raise CSVValidationError(f"Missing required columns: {', '.join(missing_fields)}")
            else:
                # If no headers, check if the number of columns matches
                if len(data.columns) < len(expected_fields):
                    raise CSVValidationError(f"CSV has {len(data.columns)} columns, but schema requires {len(expected_fields)}")
                
                # Rename columns to match schema
                data.columns = expected_fields[:len(data.columns)]
            
            # Validate data types
            for field in self.schema["fields"]:
                col_name = field["name"]
                if col_name not in data.columns:
                    continue
                    
                # Validate data type
                field_type = field["type"]
                
                try:
                    if field_type == "number" or field_type == "integer":
                        # Convert to numeric
                        data[col_name] = pd.to_numeric(data[col_name])
                        
                        # For integer, check if all values are integers
                        if field_type == "integer":
                            if not all(data[col_name].apply(lambda x: x.is_integer())):
                                raise CSVValidationError(f"Column '{col_name}' contains non-integer values")
                                
                    elif field_type == "boolean":
                        # Convert to boolean
                        data[col_name] = data[col_name].astype(bool)
                        
                    elif field_type == "date":
                        # Convert to datetime
                        data[col_name] = pd.to_datetime(data[col_name])
                        
                except Exception as e:
                    raise CSVValidationError(f"Invalid data in column '{col_name}'. Expected {field_type}: {str(e)}")
                
                # Validate constraints if present
                if "constraints" in field:
                    constraints = field["constraints"]
                    
                    # Check required constraint
                    if constraints.get("required", False):
                        if data[col_name].isnull().any():
                            raise CSVValidationError(f"Column '{col_name}' contains null values but is required")
                            
                    # Check minimum value
                    if "minimum" in constraints and field_type in ["number", "integer"]:
                        min_val = constraints["minimum"]
                        if (data[col_name] < min_val).any():
                            raise CSVValidationError(f"Column '{col_name}' contains values less than {min_val}")
                            
                    # Check maximum value
                    if "maximum" in constraints and field_type in ["number", "integer"]:
                        max_val = constraints["maximum"]
                        if (data[col_name] > max_val).any():
                            raise CSVValidationError(f"Column '{col_name}' contains values greater than {max_val}")
                            
                    # Check pattern
                    if "pattern" in constraints and field_type == "string":
                        pattern = constraints["pattern"]
                        regex = re.compile(pattern)
                        invalid_values = data[col_name][~data[col_name].astype(str).str.match(pattern)]
                        if not invalid_values.empty:
                            raise CSVValidationError(f"Column '{col_name}' contains values that don't match pattern '{pattern}'")
            
            return data
                
        except pd.errors.EmptyDataError:
            raise CSVValidationError("The CSV file is empty")
        except pd.errors.ParserError:
            raise CSVValidationError("Invalid CSV format")
        except Exception as e:
            if isinstance(e, CSVValidationError):
                raise
            raise CSVValidationError(f"CSV validation error: {str(e)}")
            
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert validated CSV to pandas DataFrame
        
        Returns:
            Pandas DataFrame containing the validated data
        """
        return self.validate() 