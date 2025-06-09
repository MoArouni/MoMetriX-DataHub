import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import base64
from io import BytesIO
from sqlalchemy import func, desc, and_
from app.models.sales import Sale
from app.models.product import Product, Embellishment
from app.models.store import Store
from app.models.product_category import ProductCategory
from flask_login import current_user

class AnalyticsService:
    def __init__(self):
        # Set up styling
        plt.style.use('default')
        sns.set_palette("husl")
        
    def get_company_sales_data(self, company_id, start_date=None, end_date=None):
        """Get sales data for analytics as a pandas DataFrame"""
        query = Sale.query.filter_by(company_id=company_id)
        
        if start_date:
            query = query.filter(Sale.sale_date >= start_date)
        if end_date:
            query = query.filter(Sale.sale_date <= end_date)
            
        sales = query.all()
        
        data = []
        for sale in sales:
            embellishment_names = [emb.name for emb in sale.embellishments]
            data.append({
                'sale_id': sale.id,
                'sale_date': sale.sale_date,
                'store_name': sale.store_name,
                'product_category': sale.product_category,
                'product_name': sale.product_name,
                'quantity': sale.quantity,
                'total': float(sale.total_amount),
                'card_amount': float(sale.card_amount or 0),
                'cash_amount': float(sale.cash_amount or 0),
                'payment_method': sale.payment_method,
                'embellishments': ', '.join(embellishment_names) if embellishment_names else 'None',
                'day_of_week': sale.sale_date.strftime('%A'),
                'month': sale.sale_date.strftime('%B'),
                'year': sale.sale_date.year
            })
        
        return pd.DataFrame(data)
    
    def _create_chart(self, fig, title):
        """Convert matplotlib figure to base64 string"""
        plt.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close(fig)
        
        graphic = base64.b64encode(image_png)
        graphic = graphic.decode('utf-8')
        return graphic
    
    # SHOP ANALYTICS
    def get_store_analytics(self, df):
        """Analytics for stores/shops"""
        if df.empty:
            return {}
            
        store_stats = df.groupby('store_name').agg({
            'total': ['sum', 'mean', 'count'],
            'quantity': 'sum'
        }).round(2)
        
        store_stats.columns = ['total_revenue', 'avg_sale', 'total_transactions', 'total_quantity']
        store_stats = store_stats.reset_index()
        
        # Charts
        charts = {}
        
        # 1. Revenue by Store (Bar Chart)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=store_stats, x='store_name', y='total_revenue', ax=ax)
        ax.set_title('Total Revenue by Store')
        ax.set_xlabel('Store')
        ax.set_ylabel('Revenue ($)')
        plt.xticks(rotation=45)
        charts['revenue_bar'] = self._create_chart(fig, 'Revenue by Store')
        
        # 2. Store Performance Heatmap
        fig, ax = plt.subplots(figsize=(8, 6))
        pivot_data = df.pivot_table(values='total', index='store_name', columns='month', aggfunc='sum', fill_value=0)
        sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
        ax.set_title('Store Performance Heatmap (Revenue by Month)')
        charts['store_heatmap'] = self._create_chart(fig, 'Store Heatmap')
        
        # 3. Store Revenue Distribution (Pie Chart)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(store_stats['total_revenue'], labels=store_stats['store_name'], autopct='%1.1f%%')
        ax.set_title('Revenue Distribution by Store')
        charts['revenue_pie'] = self._create_chart(fig, 'Revenue Distribution')
        
        return {
            'stats': store_stats.to_dict('records'),
            'charts': charts,
            'peak_store': store_stats.loc[store_stats['total_revenue'].idxmax(), 'store_name'],
            'worst_store': store_stats.loc[store_stats['total_revenue'].idxmin(), 'store_name']
        }
    
    # CATEGORY ANALYTICS
    def get_category_analytics(self, df):
        """Analytics for product categories"""
        if df.empty:
            return {}
            
        category_stats = df.groupby('product_category').agg({
            'total': ['sum', 'mean', 'count'],
            'quantity': 'sum'
        }).round(2)
        
        category_stats.columns = ['total_revenue', 'avg_sale', 'total_transactions', 'total_quantity']
        category_stats = category_stats.reset_index()
        
        charts = {}
        
        # 1. Category Performance (Horizontal Bar)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=category_stats, y='product_category', x='total_revenue', ax=ax)
        ax.set_title('Revenue by Product Category')
        ax.set_xlabel('Revenue ($)')
        charts['category_bar'] = self._create_chart(fig, 'Category Revenue')
        
        # 2. Category Trends Over Time
        fig, ax = plt.subplots(figsize=(12, 6))
        monthly_category = df.groupby(['month', 'product_category'])['total'].sum().reset_index()
        sns.lineplot(data=monthly_category, x='month', y='total', hue='product_category', ax=ax)
        ax.set_title('Category Performance Trends by Month')
        plt.xticks(rotation=45)
        charts['category_trends'] = self._create_chart(fig, 'Category Trends')
        
        # 3. Category Quantity vs Revenue Scatter
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.scatterplot(data=category_stats, x='total_quantity', y='total_revenue', 
                       size='total_transactions', sizes=(50, 500), ax=ax)
        for i, row in category_stats.iterrows():
            ax.annotate(row['product_category'], (row['total_quantity'], row['total_revenue']))
        ax.set_title('Category Analysis: Quantity vs Revenue')
        charts['category_scatter'] = self._create_chart(fig, 'Category Scatter')
        
        return {
            'stats': category_stats.to_dict('records'),
            'charts': charts,
            'peak_category': category_stats.loc[category_stats['total_revenue'].idxmax(), 'product_category'],
            'worst_category': category_stats.loc[category_stats['total_revenue'].idxmin(), 'product_category']
        }
    
    # PRODUCT ANALYTICS
    def get_product_analytics(self, df):
        """Analytics for individual products"""
        if df.empty:
            return {}
            
        product_stats = df.groupby('product_name').agg({
            'total': ['sum', 'mean', 'count'],
            'quantity': 'sum'
        }).round(2)
        
        product_stats.columns = ['total_revenue', 'avg_sale', 'total_transactions', 'total_quantity']
        product_stats = product_stats.reset_index()
        
        # Get top 10 and bottom 10
        top_products = product_stats.nlargest(10, 'total_revenue')
        bottom_products = product_stats.nsmallest(10, 'total_revenue')
        
        charts = {}
        
        # 1. Top 10 Products (Bar Chart)
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.barplot(data=top_products, x='total_revenue', y='product_name', ax=ax)
        ax.set_title('Top 10 Products by Revenue')
        ax.set_xlabel('Revenue ($)')
        charts['top_products'] = self._create_chart(fig, 'Top Products')
        
        # 2. Product Performance Distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(product_stats['total_revenue'], bins=20, alpha=0.7, edgecolor='black')
        ax.set_title('Product Revenue Distribution')
        ax.set_xlabel('Revenue ($)')
        ax.set_ylabel('Number of Products')
        charts['product_dist'] = self._create_chart(fig, 'Product Distribution')
        
        # 3. Product Sales Frequency
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(product_stats['total_transactions'], bins=15, alpha=0.7, edgecolor='black')
        ax.set_title('Product Sales Frequency Distribution')
        ax.set_xlabel('Number of Transactions')
        ax.set_ylabel('Number of Products')
        charts['frequency_dist'] = self._create_chart(fig, 'Frequency Distribution')
        
        return {
            'top_products': top_products.to_dict('records'),
            'bottom_products': bottom_products.to_dict('records'),
            'total_products': len(product_stats),
            'charts': charts,
            'peak_product': product_stats.loc[product_stats['total_revenue'].idxmax(), 'product_name'],
            'worst_product': product_stats.loc[product_stats['total_revenue'].idxmin(), 'product_name']
        }
    
    # PAYMENT METHOD ANALYTICS
    def get_payment_analytics(self, df):
        """Analytics for cash vs card payments"""
        if df.empty:
            return {}
            
        payment_stats = df.groupby('payment_method').agg({
            'total': ['sum', 'mean', 'count']
        }).round(2)
        
        payment_stats.columns = ['total_revenue', 'avg_transaction', 'transaction_count']
        payment_stats = payment_stats.reset_index()
        
        charts = {}
        
        # 1. Payment Method Distribution (Pie Chart)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(payment_stats['total_revenue'], labels=payment_stats['payment_method'], autopct='%1.1f%%')
        ax.set_title('Revenue by Payment Method')
        charts['payment_pie'] = self._create_chart(fig, 'Payment Distribution')
        
        # 2. Payment Method Trends
        fig, ax = plt.subplots(figsize=(12, 6))
        daily_payments = df.groupby(['sale_date', 'payment_method'])['total'].sum().reset_index()
        sns.lineplot(data=daily_payments, x='sale_date', y='total', hue='payment_method', ax=ax)
        ax.set_title('Payment Method Trends Over Time')
        plt.xticks(rotation=45)
        charts['payment_trends'] = self._create_chart(fig, 'Payment Trends')
        
        # 3. Average Transaction by Payment Method
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(data=payment_stats, x='payment_method', y='avg_transaction', ax=ax)
        ax.set_title('Average Transaction Value by Payment Method')
        ax.set_ylabel('Average Transaction ($)')
        charts['avg_payment'] = self._create_chart(fig, 'Average Payment')
        
        return {
            'stats': payment_stats.to_dict('records'),
            'charts': charts
        }
    
    # EMBELLISHMENT ANALYTICS
    def get_embellishment_analytics(self, df):
        """Analytics for embellishments"""
        if df.empty:
            return {}
        
        # Filter out 'None' embellishments and split multiple embellishments
        embellishment_data = []
        for _, row in df.iterrows():
            if row['embellishments'] != 'None':
                embs = row['embellishments'].split(', ')
                for emb in embs:
                    embellishment_data.append({
                        'embellishment': emb.strip(),
                        'total': row['total'],
                        'quantity': row['quantity'],
                        'sale_date': row['sale_date']
                    })
        
        if not embellishment_data:
            return {'message': 'No embellishment data available'}
        
        emb_df = pd.DataFrame(embellishment_data)
        
        emb_stats = emb_df.groupby('embellishment').agg({
            'total': ['sum', 'mean', 'count'],
            'quantity': 'sum'
        }).round(2)
        
        emb_stats.columns = ['total_revenue', 'avg_sale', 'usage_count', 'total_quantity']
        emb_stats = emb_stats.reset_index()
        
        charts = {}
        
        # 1. Top Embellishments (Bar Chart)
        fig, ax = plt.subplots(figsize=(10, 6))
        top_embs = emb_stats.nlargest(10, 'total_revenue')
        sns.barplot(data=top_embs, x='total_revenue', y='embellishment', ax=ax)
        ax.set_title('Top Embellishments by Revenue')
        ax.set_xlabel('Revenue ($)')
        charts['top_embellishments'] = self._create_chart(fig, 'Top Embellishments')
        
        # 2. Embellishment Usage Frequency
        fig, ax = plt.subplots(figsize=(10, 6))
        usage_top = emb_stats.nlargest(10, 'usage_count')
        sns.barplot(data=usage_top, x='usage_count', y='embellishment', ax=ax)
        ax.set_title('Most Used Embellishments')
        ax.set_xlabel('Number of Uses')
        charts['embellishment_usage'] = self._create_chart(fig, 'Embellishment Usage')
        
        # 3. Embellishment Revenue vs Usage Scatter
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.scatterplot(data=emb_stats, x='usage_count', y='total_revenue', 
                       size='avg_sale', sizes=(50, 300), ax=ax)
        ax.set_title('Embellishment Performance: Usage vs Revenue')
        charts['emb_scatter'] = self._create_chart(fig, 'Embellishment Scatter')
        
        return {
            'stats': emb_stats.to_dict('records'),
            'charts': charts,
            'peak_embellishment': emb_stats.loc[emb_stats['total_revenue'].idxmax(), 'embellishment'],
            'worst_embellishment': emb_stats.loc[emb_stats['total_revenue'].idxmin(), 'embellishment']
        }
    
    # DAY OF WEEK ANALYTICS
    def get_day_analytics(self, df):
        """Analytics for days of the week"""
        if df.empty:
            return {}
            
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        day_stats = df.groupby('day_of_week').agg({
            'total': ['sum', 'mean', 'count']
        }).round(2)
        
        day_stats.columns = ['total_revenue', 'avg_sale', 'transaction_count']
        day_stats = day_stats.reset_index()
        
        # Reorder by day of week
        day_stats['day_order'] = day_stats['day_of_week'].map({day: i for i, day in enumerate(day_order)})
        day_stats = day_stats.sort_values('day_order').drop('day_order', axis=1)
        
        charts = {}
        
        # 1. Revenue by Day (Line Chart)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(data=day_stats, x='day_of_week', y='total_revenue', marker='o', ax=ax)
        ax.set_title('Revenue by Day of Week')
        ax.set_ylabel('Revenue ($)')
        plt.xticks(rotation=45)
        charts['day_line'] = self._create_chart(fig, 'Day Revenue Line')
        
        # 2. Day Performance Heatmap
        fig, ax = plt.subplots(figsize=(10, 6))
        pivot_day = df.pivot_table(values='total', index='day_of_week', columns='month', 
                                  aggfunc='sum', fill_value=0)
        # Reorder rows by day of week
        pivot_day = pivot_day.reindex(day_order)
        sns.heatmap(pivot_day, annot=True, fmt='.0f', cmap='Blues', ax=ax)
        ax.set_title('Daily Performance Heatmap (Revenue by Month)')
        charts['day_heatmap'] = self._create_chart(fig, 'Day Heatmap')
        
        # 3. Transaction Count by Day
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=day_stats, x='day_of_week', y='transaction_count', ax=ax)
        ax.set_title('Number of Transactions by Day')
        ax.set_ylabel('Transaction Count')
        plt.xticks(rotation=45)
        charts['day_transactions'] = self._create_chart(fig, 'Day Transactions')
        
        return {
            'stats': day_stats.to_dict('records'),
            'charts': charts,
            'peak_day': day_stats.loc[day_stats['total_revenue'].idxmax(), 'day_of_week'],
            'worst_day': day_stats.loc[day_stats['total_revenue'].idxmin(), 'day_of_week']
        }
    
    # MONTHLY ANALYTICS
    def get_monthly_analytics(self, df):
        """Analytics for months of the year"""
        if df.empty:
            return {}
            
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        month_stats = df.groupby('month').agg({
            'total': ['sum', 'mean', 'count']
        }).round(2)
        
        month_stats.columns = ['total_revenue', 'avg_sale', 'transaction_count']
        month_stats = month_stats.reset_index()
        
        # Reorder by month
        month_stats['month_order'] = month_stats['month'].map({month: i for i, month in enumerate(month_order)})
        month_stats = month_stats.sort_values('month_order').drop('month_order', axis=1)
        
        charts = {}
        
        # 1. Monthly Revenue Trend
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(data=month_stats, x='month', y='total_revenue', marker='o', linewidth=3, ax=ax)
        ax.set_title('Monthly Revenue Trend')
        ax.set_ylabel('Revenue ($)')
        plt.xticks(rotation=45)
        charts['monthly_trend'] = self._create_chart(fig, 'Monthly Trend')
        
        # 2. Monthly Performance (Bar Chart)
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.barplot(data=month_stats, x='month', y='total_revenue', ax=ax)
        ax.set_title('Revenue by Month')
        ax.set_ylabel('Revenue ($)')
        plt.xticks(rotation=45)
        charts['monthly_bar'] = self._create_chart(fig, 'Monthly Bar')
        
        # 3. Monthly Growth Rate
        month_stats['growth_rate'] = month_stats['total_revenue'].pct_change() * 100
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.barplot(data=month_stats[1:], x='month', y='growth_rate', ax=ax)
        ax.set_title('Month-over-Month Growth Rate (%)')
        ax.set_ylabel('Growth Rate (%)')
        ax.axhline(y=0, color='red', linestyle='--')
        plt.xticks(rotation=45)
        charts['growth_rate'] = self._create_chart(fig, 'Growth Rate')
        
        return {
            'stats': month_stats.to_dict('records'),
            'charts': charts,
            'peak_month': month_stats.loc[month_stats['total_revenue'].idxmax(), 'month'],
            'worst_month': month_stats.loc[month_stats['total_revenue'].idxmin(), 'month']
        }
    
    # DASHBOARD SUMMARY
    def get_dashboard_summary(self, df):
        """Get key metrics for dashboard"""
        if df.empty:
            return {}
        
        # Convert dates to pandas datetime for consistent comparison
        today = pd.Timestamp.now().normalize()
        yesterday = today - pd.Timedelta(days=1)
        this_week_start = today - pd.Timedelta(days=today.weekday())
        last_week_start = this_week_start - pd.Timedelta(days=7)
        this_month_start = today.replace(day=1)
        
        # Convert sale_date to datetime for filtering
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        
        # Calculate key metrics
        total_revenue = df['total'].sum()
        total_transactions = len(df)
        avg_transaction = df['total'].mean()
        
        # Time-based comparisons - using pandas datetime comparison
        today_sales = df[df['sale_date'].dt.normalize() == today]['total'].sum()
        yesterday_sales = df[df['sale_date'].dt.normalize() == yesterday]['total'].sum()
        
        this_week_sales = df[df['sale_date'].dt.normalize() >= this_week_start]['total'].sum()
        last_week_sales = df[(df['sale_date'].dt.normalize() >= last_week_start) & 
                           (df['sale_date'].dt.normalize() < this_week_start)]['total'].sum()
        
        this_month_sales = df[df['sale_date'].dt.normalize() >= this_month_start]['total'].sum()
        
        # Top performers - handle empty groups
        try:
            top_product = df.groupby('product_name')['total'].sum().idxmax()
        except ValueError:
            top_product = "No products"
            
        try:
            top_store = df.groupby('store_name')['total'].sum().idxmax()
        except ValueError:
            top_store = "No stores"
        
        # Create summary chart
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Daily trend (last 30 days)
        thirty_days_ago = today - pd.Timedelta(days=30)
        last_30_days = df[df['sale_date'].dt.normalize() >= thirty_days_ago]
        if not last_30_days.empty:
            daily_trend = last_30_days.groupby(last_30_days['sale_date'].dt.date)['total'].sum()
            ax1.plot(daily_trend.index, daily_trend.values, marker='o')
            ax1.set_title('Last 30 Days Revenue Trend')
            ax1.set_ylabel('Revenue ($)')
            ax1.tick_params(axis='x', rotation=45)
        else:
            ax1.text(0.5, 0.5, 'No data available', transform=ax1.transAxes, 
                    ha='center', va='center', fontsize=12)
            ax1.set_title('Last 30 Days Revenue Trend')
        
        # Top 5 products
        if not df.empty:
            top_products = df.groupby('product_name')['total'].sum().nlargest(5)
            if not top_products.empty:
                ax2.barh(range(len(top_products)), top_products.values)
                ax2.set_yticks(range(len(top_products)))
                ax2.set_yticklabels(top_products.index)
                ax2.set_title('Top 5 Products')
                ax2.set_xlabel('Revenue ($)')
            else:
                ax2.text(0.5, 0.5, 'No products', transform=ax2.transAxes, 
                        ha='center', va='center', fontsize=12)
                ax2.set_title('Top 5 Products')
        
        # Payment method distribution
        if not df.empty:
            payment_dist = df.groupby('payment_method')['total'].sum()
            if not payment_dist.empty:
                ax3.pie(payment_dist.values, labels=payment_dist.index, autopct='%1.1f%%')
                ax3.set_title('Payment Method Distribution')
            else:
                ax3.text(0.5, 0.5, 'No payment data', transform=ax3.transAxes, 
                        ha='center', va='center', fontsize=12)
                ax3.set_title('Payment Method Distribution')
        
        # Store performance
        if not df.empty:
            store_perf = df.groupby('store_name')['total'].sum()
            if not store_perf.empty:
                ax4.bar(store_perf.index, store_perf.values)
                ax4.set_title('Store Performance')
                ax4.set_ylabel('Revenue ($)')
                ax4.tick_params(axis='x', rotation=45)
            else:
                ax4.text(0.5, 0.5, 'No store data', transform=ax4.transAxes, 
                        ha='center', va='center', fontsize=12)
                ax4.set_title('Store Performance')
        
        plt.tight_layout()
        summary_chart = self._create_chart(fig, 'Dashboard Summary')
        
        return {
            'total_revenue': round(total_revenue, 2),
            'total_transactions': total_transactions,
            'avg_transaction': round(avg_transaction, 2),
            'today_sales': round(today_sales, 2),
            'yesterday_sales': round(yesterday_sales, 2),
            'this_week_sales': round(this_week_sales, 2),
            'last_week_sales': round(last_week_sales, 2),
            'this_month_sales': round(this_month_sales, 2),
            'top_product': top_product,
            'top_store': top_store,
            'daily_change': round(((today_sales - yesterday_sales) / (yesterday_sales or 1)) * 100, 1),
            'weekly_change': round(((this_week_sales - last_week_sales) / (last_week_sales or 1)) * 100, 1),
            'summary_chart': summary_chart
        }
    
    # REPORTS GENERATION
    def generate_reports(self, df):
        """Generate performance reports"""
        if df.empty:
            return {}
        
        # Best and worst performers
        product_performance = df.groupby('product_name')['total'].sum().sort_values(ascending=False)
        category_performance = df.groupby('product_category')['total'].sum().sort_values(ascending=False)
        store_performance = df.groupby('store_name')['total'].sum().sort_values(ascending=False)
        
        # Embellishment performance
        embellishment_data = []
        for _, row in df.iterrows():
            if row['embellishments'] != 'None':
                embs = row['embellishments'].split(', ')
                for emb in embs:
                    embellishment_data.append({'embellishment': emb.strip(), 'total': row['total']})
        
        if embellishment_data:
            emb_df = pd.DataFrame(embellishment_data)
            embellishment_performance = emb_df.groupby('embellishment')['total'].sum().sort_values(ascending=False)
        else:
            embellishment_performance = pd.Series(dtype=float)
        
        # Day performance
        day_performance = df.groupby('day_of_week')['total'].sum().sort_values(ascending=False)
        
        return {
            'best_products': product_performance.head(10).to_dict(),
            'worst_products': product_performance.tail(10).to_dict(),
            'best_categories': category_performance.head(5).to_dict(),
            'worst_categories': category_performance.tail(5).to_dict(),
            'best_stores': store_performance.head(10).to_dict(),
            'worst_stores': store_performance.tail(10).to_dict(),
            'best_embellishments': embellishment_performance.head(10).to_dict() if not embellishment_performance.empty else {},
            'worst_embellishments': embellishment_performance.tail(10).to_dict() if not embellishment_performance.empty else {},
            'best_days': day_performance.head(7).to_dict(),
            'worst_days': day_performance.tail(7).to_dict()
        }