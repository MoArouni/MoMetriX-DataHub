import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple
import io
import base64

class AnalysisEngine:
    """
    Service for generating various data analyses and visualizations.
    This class is responsible for processing data and creating charts, graphs, and dashboards.
    """
    
    @staticmethod
    def generate_chart(data: pd.DataFrame, config: Dict[str, Any]) -> str:
        """
        Generate a chart based on the provided data and configuration
        
        Args:
            data: Pandas DataFrame containing the data
            config: Dictionary with chart configuration
                - chart_type: bar, line, pie, scatter, table
                - x_axis: column name for x-axis
                - y_axis: column name for y-axis
                - grouping: column name for grouping (optional)
                - aggregation: aggregation method (sum, avg, count, min, max)
                
        Returns:
            Base64 encoded image of the chart
        """
        if not data.size:
            raise ValueError("No data provided for chart generation")
            
        chart_type = config.get('chart_type')
        x_axis = config.get('x_axis')
        y_axis = config.get('y_axis')
        grouping = config.get('grouping')
        aggregation = config.get('aggregation', 'sum')
        
        # Validate inputs
        if not chart_type or not x_axis:
            raise ValueError("Chart type and x-axis must be specified")
            
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Prepare data for visualization
        if grouping:
            # Group by the specified column
            if aggregation == 'sum':
                agg_data = data.groupby([x_axis, grouping])[y_axis].sum().unstack()
            elif aggregation == 'avg':
                agg_data = data.groupby([x_axis, grouping])[y_axis].mean().unstack()
            elif aggregation == 'count':
                agg_data = data.groupby([x_axis, grouping])[y_axis].count().unstack()
            elif aggregation == 'min':
                agg_data = data.groupby([x_axis, grouping])[y_axis].min().unstack()
            elif aggregation == 'max':
                agg_data = data.groupby([x_axis, grouping])[y_axis].max().unstack()
            else:
                agg_data = data.groupby([x_axis, grouping])[y_axis].sum().unstack()
            
            # Generate the chart
            if chart_type == 'bar':
                agg_data.plot(kind='bar', ax=plt.gca())
            elif chart_type == 'line':
                agg_data.plot(kind='line', ax=plt.gca())
            else:
                # For other chart types, use the first group only
                agg_data.iloc[:, 0].plot(kind=chart_type, ax=plt.gca())
        else:
            # Without grouping
            if aggregation == 'sum':
                agg_data = data.groupby(x_axis)[y_axis].sum()
            elif aggregation == 'avg':
                agg_data = data.groupby(x_axis)[y_axis].mean()
            elif aggregation == 'count':
                agg_data = data.groupby(x_axis)[y_axis].count()
            elif aggregation == 'min':
                agg_data = data.groupby(x_axis)[y_axis].min()
            elif aggregation == 'max':
                agg_data = data.groupby(x_axis)[y_axis].max()
            else:
                agg_data = data.groupby(x_axis)[y_axis].sum()
            
            # Generate the chart
            if chart_type == 'scatter':
                # Scatter plot is a special case
                plt.scatter(data[x_axis], data[y_axis])
            else:
                agg_data.plot(kind=chart_type, ax=plt.gca())
        
        # Set labels
        plt.xlabel(x_axis)
        plt.ylabel(y_axis)
        plt.title(f"{aggregation.capitalize()} of {y_axis} by {x_axis}")
        plt.tight_layout()
        
        # Convert plot to base64 image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
        
    @staticmethod
    def generate_summary_stats(data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for the dataset
        
        Args:
            data: Pandas DataFrame containing the data
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {}
        
        # Basic count
        summary['row_count'] = len(data)
        summary['column_count'] = len(data.columns)
        
        # Numeric columns statistics
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if not numeric_cols.empty:
            summary['numeric_stats'] = {}
            for col in numeric_cols:
                summary['numeric_stats'][col] = {
                    'min': data[col].min(),
                    'max': data[col].max(),
                    'mean': data[col].mean(),
                    'median': data[col].median(),
                    'std': data[col].std()
                }
        
        # Categorical columns statistics
        cat_cols = data.select_dtypes(exclude=[np.number]).columns
        if not cat_cols.empty:
            summary['categorical_stats'] = {}
            for col in cat_cols:
                value_counts = data[col].value_counts()
                summary['categorical_stats'][col] = {
                    'unique_count': data[col].nunique(),
                    'most_common': value_counts.index[0] if not value_counts.empty else None,
                    'most_common_count': value_counts.iloc[0] if not value_counts.empty else 0
                }
        
        return summary 