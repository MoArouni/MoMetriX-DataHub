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
import re

class AnalyticsService:
    def __init__(self):
        # Set up styling for website theme
        plt.style.use('default')
        
        # Use website theme colors
        self.theme_colors = ['#007bff', '#6f42c1', '#e83e8c', '#20c997', '#fd7e14', '#ffc107']
        sns.set_palette(self.theme_colors)
        
        # Heatmap colormap matching website theme
        self.heatmap_cmap = sns.blend_palette(['#f8f9fa', '#007bff', '#0056b3'], as_cmap=True)
        
    def extract_embellishments_from_notes(self, notes):
        """Extract embellishment names from sale notes"""
        if not notes:
            return []
            
        # Look for embellishments in the format "Details: ..."
        match = re.search(r'Details:\s*(.*?)(?:\n|$)', notes)
        if not match:
            return []
            
        details = match.group(1)
        # Split by common separators and clean up
        embellishments = [e.strip() for e in re.split(r'[,;]|\band\b', details)]
        # Remove empty strings and duplicates
        return list(set(e for e in embellishments if e))
    
    def auto_create_from_sales(self, company_id, create_products=True, create_embellishments=True):
        """Auto-create products and/or embellishments from sales data with improved duplicate handling and bad value filtering"""
        from app import db
        from app.models.sales import Sale
        from app.models.product import Product, Embellishment
        from app.models.product_category import ProductCategory
        import re
        
        # Expanded bad values to filter out
        BAD_VALUES = {
            'na', 'n/a', 'n.a.', 'none', 'null', 'unknown', 'other', 'misc', 'miscellaneous', 
            'etc', 'etc.', 'various', 'mixed', 'assorted', 'general', 'default', 'temp', 
            'temporary', 'test', 'sample', 'example', 'placeholder', 'tbd', 'tba', 'pending',
            'blank', 'empty', 'void', 'nil', 'nothing', 'no data', 'nodata', 'missing',
            'untitled', 'unnamed', 'no name', 'noname', 'item', 'product', 'thing'
        }
        
        # Get all sales for the company
        sales = Sale.query.filter_by(company_id=company_id).all()
        
        # Track created items to avoid duplicates
        created_products = set()
        created_embellishments = set()
        product_categories = {}  # Cache for category lookups
        
        def clean_name(name):
            """Clean and normalize a name for comparison"""
            if not name or not isinstance(name, str):
                return None
            
            # Convert to lowercase and strip
            name = name.lower().strip()
            
            # Remove extra whitespace and normalize
            name = re.sub(r'\s+', ' ', name)
            
            # Skip if it's a bad value
            if name in BAD_VALUES:
                return None
            
            # Skip if it's too short or too long
            if len(name) < 2 or len(name) > 100:
                return None
            
            # Skip if it's just numbers or special characters
            if re.match(r'^[\d\s\-_.,;:!@#$%^&*()+=\[\]{}|\\/<>?~`]+$', name):
                return None
            
            # Skip repetitive patterns (like "aaa", "111", "xxx")
            if len(set(name.replace(' ', ''))) <= 2 and len(name) > 3:
                return None
            
            # Remove common prefixes/suffixes that don't add value
            prefixes_to_remove = ['the ', 'a ', 'an ', 'item ', 'product ']
            suffixes_to_remove = [' item', ' product', ' thing']
            
            for prefix in prefixes_to_remove:
                if name.startswith(prefix):
                    name = name[len(prefix):].strip()
            
            for suffix in suffixes_to_remove:
                if name.endswith(suffix):
                    name = name[:-len(suffix)].strip()
            
            # Final check after cleaning
            if not name or name in BAD_VALUES:
                return None
                
            return name.title()  # Return in title case for consistency
        
        def normalize_for_comparison(name):
            """Normalize name for similarity comparison"""
            if not name:
                return None
            
            # Convert to lowercase, remove special chars, normalize spaces
            normalized = re.sub(r'[^\w\s]', '', name.lower())
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            # Remove common words that don't help with uniqueness
            common_words = {'and', 'or', 'with', 'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'by'}
            words = [word for word in normalized.split() if word not in common_words]
            
            return ' '.join(words)
        
        def is_similar_name(name1, name2, threshold=0.8):
            """Check if two names are similar using simple string comparison"""
            if not name1 or not name2:
                return False
            
            norm1 = normalize_for_comparison(name1)
            norm2 = normalize_for_comparison(name2)
            
            if not norm1 or not norm2:
                return False
            
            # Exact match after normalization
            if norm1 == norm2:
                return True
            
            # Check if one is contained in the other
            if norm1 in norm2 or norm2 in norm1:
                return True
            
            # Simple similarity check based on common words
            words1 = set(norm1.split())
            words2 = set(norm2.split())
            
            if not words1 or not words2:
                return False
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            similarity = intersection / union if union > 0 else 0
            return similarity >= threshold
        
        stats = {
            'products_created': 0,
            'embellishments_created': 0,
            'categories_created': 0,
            'products_skipped': 0,
            'embellishments_skipped': 0
        }
        
        for sale in sales:
            # Process product categories
            if sale.product_category:
                clean_category = clean_name(sale.product_category)
                if clean_category and clean_category not in product_categories:
                    # Check if similar category already exists
                    existing_categories = ProductCategory.query.filter_by(company_id=company_id).all()
                    similar_found = False
                    
                    for existing in existing_categories:
                        if is_similar_name(clean_category, existing.name):
                            product_categories[clean_category] = existing
                            similar_found = True
                            break
                    
                    if not similar_found:
                        category = ProductCategory(
                            name=clean_category,
                            company_id=company_id
                        )
                        db.session.add(category)
                        db.session.flush()
                        product_categories[clean_category] = category
                        stats['categories_created'] += 1
            
            # Process products
            if create_products and sale.product_name:
                clean_product_name = clean_name(sale.product_name)
                if clean_product_name:
                    # Normalize for comparison
                    normalized_name = normalize_for_comparison(clean_product_name)
                    
                    if normalized_name and normalized_name not in created_products:
                        # Check if similar product already exists
                        existing_products = Product.query.filter_by(company_id=company_id).all()
                        similar_found = False
                        
                        for existing in existing_products:
                            if is_similar_name(clean_product_name, existing.name):
                                similar_found = True
                                stats['products_skipped'] += 1
                                break
                        
                        if not similar_found:
                            category_id = None
                            if sale.product_category:
                                clean_cat = clean_name(sale.product_category)
                                if clean_cat in product_categories:
                                    category_id = product_categories[clean_cat].id
                            
                            # Calculate base price safely
                            base_price = 0
                            if sale.quantity and sale.quantity > 0 and sale.total:
                                try:
                                    base_price = float(sale.total) / float(sale.quantity)
                                except (ValueError, ZeroDivisionError):
                                    base_price = float(sale.total) if sale.total else 0
                            
                            product = Product(
                                name=clean_product_name,
                                category_id=category_id,
                                company_id=company_id,
                                base_price=base_price
                            )
                            db.session.add(product)
                            db.session.flush()
                            created_products.add(normalized_name)
                            stats['products_created'] += 1
            
            # Process embellishments from notes
            if create_embellishments and sale.notes:
                # Split notes by common delimiters
                potential_embellishments = re.split(r'[,;|\n]+', sale.notes)
                
                for emb_text in potential_embellishments:
                    clean_emb_name = clean_name(emb_text)
                    if clean_emb_name:
                        normalized_emb = normalize_for_comparison(clean_emb_name)
                        
                        if normalized_emb and normalized_emb not in created_embellishments:
                            # Check if similar embellishment already exists
                            existing_embellishments = Embellishment.query.filter_by(company_id=company_id).all()
                            similar_found = False
                            
                            for existing in existing_embellishments:
                                if is_similar_name(clean_emb_name, existing.name):
                                    similar_found = True
                                    stats['embellishments_skipped'] += 1
                                    break
                            
                            if not similar_found:
                                emb = Embellishment(
                                    name=clean_emb_name,
                                    company_id=company_id,
                                    description=f"Auto-created from sales data"
                                )
                                db.session.add(emb)
                                db.session.flush()
                                
                                # Associate with product category if available
                                if sale.product_category:
                                    clean_cat = clean_name(sale.product_category)
                                    if clean_cat in product_categories:
                                        category = product_categories[clean_cat]
                                        if category not in emb.product_types:
                                            emb.product_types.append(category)
                                
                                created_embellishments.add(normalized_emb)
                                stats['embellishments_created'] += 1
        
        try:
            db.session.commit()
            
            # Build success message
            messages = []
            if create_products:
                messages.append(f"Created {stats['products_created']} products (skipped {stats['products_skipped']} duplicates)")
            if create_embellishments:
                messages.append(f"Created {stats['embellishments_created']} embellishments (skipped {stats['embellishments_skipped']} duplicates)")
            if stats['categories_created'] > 0:
                messages.append(f"Created {stats['categories_created']} categories")
            
            return {
                'success': True,
                'message': '. '.join(messages) if messages else 'No new items created',
                'stats': stats
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
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
                'year': sale.sale_date.year,
                'notes': sale.notes  # Add notes for embellishment extraction
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
        
        # Calculate percentages
        total_revenue = store_stats['total_revenue'].sum()
        total_transactions = store_stats['total_transactions'].sum()
        total_quantity = store_stats['total_quantity'].sum()
        
        store_stats['revenue_percentage'] = (store_stats['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
        store_stats['transaction_percentage'] = (store_stats['total_transactions'] / total_transactions * 100) if total_transactions > 0 else 0
        store_stats['quantity_percentage'] = (store_stats['total_quantity'] / total_quantity * 100) if total_quantity > 0 else 0
        
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
        sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap=self.heatmap_cmap, ax=ax)
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
        
        # Calculate percentages
        total_revenue = category_stats['total_revenue'].sum()
        total_transactions = category_stats['total_transactions'].sum()
        total_quantity = category_stats['total_quantity'].sum()
        
        category_stats['revenue_percentage'] = (category_stats['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
        category_stats['transaction_percentage'] = (category_stats['total_transactions'] / total_transactions * 100) if total_transactions > 0 else 0
        category_stats['quantity_percentage'] = (category_stats['total_quantity'] / total_quantity * 100) if total_quantity > 0 else 0
        
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
            return {'no_data': True, 'stats': [], 'charts': {}}
            
        product_stats = df.groupby('product_name').agg({
            'total': ['sum', 'mean', 'count'],
            'quantity': 'sum',
            'product_category': 'first'  # Get category for each product
        }).round(2)
        
        product_stats.columns = ['total_revenue', 'avg_price', 'total_transactions', 'total_quantity', 'product_category']
        product_stats = product_stats.reset_index()
        
        # Ensure we have data
        if len(product_stats) == 0:
            return {'no_data': True, 'stats': [], 'charts': {}}
        
        # Calculate percentages
        total_revenue = product_stats['total_revenue'].sum()
        total_transactions = product_stats['total_transactions'].sum()
        total_quantity = product_stats['total_quantity'].sum()
        
        product_stats['revenue_percentage'] = (product_stats['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
        product_stats['transaction_percentage'] = (product_stats['total_transactions'] / total_transactions * 100) if total_transactions > 0 else 0
        product_stats['quantity_percentage'] = (product_stats['total_quantity'] / total_quantity * 100) if total_quantity > 0 else 0
        
        # Get top 10 and bottom 10
        top_products = product_stats.nlargest(min(10, len(product_stats)), 'total_revenue')
        bottom_products = product_stats.nsmallest(min(10, len(product_stats)), 'total_revenue')
        
        charts = {}
        
        try:
            # 1. Top 10 Products (Bar Chart)
            if len(top_products) > 0:
                fig, ax = plt.subplots(figsize=(12, 6))
                sns.barplot(data=top_products, x='total_revenue', y='product_name', ax=ax)
                ax.set_title('Top Products by Revenue')
                ax.set_xlabel('Revenue ($)')
                charts['top_products'] = self._create_chart(fig, 'Top Products')
            
            # 2. Bottom 10 Products (Bar Chart) 
            if len(bottom_products) > 0:
                fig, ax = plt.subplots(figsize=(12, 6))
                sns.barplot(data=bottom_products, x='total_revenue', y='product_name', ax=ax)
                ax.set_title('Bottom Products by Revenue')
                ax.set_xlabel('Revenue ($)')
                charts['bottom_products'] = self._create_chart(fig, 'Bottom Products')
            
            # 3. Product Performance Distribution
            if len(product_stats) > 1:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.hist(product_stats['total_revenue'], bins=min(20, len(product_stats)), alpha=0.7, edgecolor='black')
                ax.set_title('Product Revenue Distribution')
                ax.set_xlabel('Revenue ($)')
                ax.set_ylabel('Number of Products')
                charts['product_distribution'] = self._create_chart(fig, 'Product Distribution')
        except Exception as e:
            print(f"Error creating product charts: {e}")
        
        # Safe calculation of metrics
        peak_product = product_stats.loc[product_stats['total_revenue'].idxmax(), 'product_name'] if len(product_stats) > 0 else 'None'
        worst_product = product_stats.loc[product_stats['total_revenue'].idxmin(), 'product_name'] if len(product_stats) > 0 else 'None'
        avg_product_revenue = product_stats['total_revenue'].mean() if len(product_stats) > 0 else 0
        
        return {
            'stats': product_stats.to_dict('records'),
            'charts': charts,
            'peak_product': peak_product,
            'worst_product': worst_product,
            'avg_product_revenue': avg_product_revenue
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
        
        # Calculate cash vs card totals
        cash_total = df[df['payment_method'] == 'Cash']['total'].sum()
        card_total = df[df['payment_method'] == 'Card']['total'].sum()
        total_revenue = cash_total + card_total
        
        cash_count = len(df[df['payment_method'] == 'Cash'])
        card_count = len(df[df['payment_method'] == 'Card'])
        
        cash_avg = cash_total / cash_count if cash_count > 0 else 0
        card_avg = card_total / card_count if card_count > 0 else 0
        
        cash_percentage = (cash_total / total_revenue * 100) if total_revenue > 0 else 0
        card_percentage = (card_total / total_revenue * 100) if total_revenue > 0 else 0
        
        # 3. Revenue Comparison Chart
        fig, ax = plt.subplots(figsize=(10, 6))
        comparison_data = pd.DataFrame({
            'Payment Method': ['Cash', 'Card'],
            'Total Revenue': [cash_total, card_total]
        })
        sns.barplot(data=comparison_data, x='Payment Method', y='Total Revenue', ax=ax)
        ax.set_title('Cash vs Card Revenue Comparison')
        ax.set_ylabel('Revenue ($)')
        charts['payment_comparison'] = self._create_chart(fig, 'Payment Comparison')
        
        return {
            'stats': payment_stats.to_dict('records'),
            'charts': charts,
            'cash_total': cash_total,
            'card_total': card_total,
            'cash_count': cash_count,
            'card_count': card_count,
            'cash_avg': cash_avg,
            'card_avg': card_avg,
            'cash_percentage': cash_percentage,
            'card_percentage': card_percentage
        }
    
    # EMBELLISHMENT ANALYTICS
    def get_embellishment_analytics(self, df):
        """Analytics for embellishments"""
        try:
            if df.empty:
                return {'no_data': True, 'stats': [], 'charts': {}}
            
            # Ensure required columns exist
            required_columns = ['embellishments', 'total', 'quantity', 'sale_date']
            if not all(col in df.columns for col in required_columns):
                print("Missing required columns for embellishment analytics")
                return {'no_data': True, 'stats': [], 'charts': {}}
            
            # Filter out 'None' embellishments and split multiple embellishments
            embellishment_data = []
            for _, row in df.iterrows():
                try:
                    if pd.notna(row['embellishments']) and row['embellishments'] != 'None' and str(row['embellishments']).strip():
                        embs = str(row['embellishments']).split(',')
                        for emb in embs:
                            emb = emb.strip()
                            if emb:  # Only add non-empty embellishments
                                embellishment_data.append({
                                    'embellishment': emb,
                                    'total': float(row['total']),
                                    'quantity': int(row['quantity']),
                                    'sale_date': row['sale_date']
                                })
                except (ValueError, TypeError) as e:
                    print(f"Error processing row in embellishment analytics: {e}")
                    continue
            
            if not embellishment_data:
                return {
                    'no_data': True,
                    'stats': [],
                    'charts': {},
                    'peak_embellishment': 'No embellishments used',
                    'embellishment_usage_rate': 0,
                    'avg_embellishment_revenue': 0
                }
            
            try:
                emb_df = pd.DataFrame(embellishment_data)
                
                # Ensure numeric columns are properly typed
                emb_df['total'] = pd.to_numeric(emb_df['total'], errors='coerce')
                emb_df['quantity'] = pd.to_numeric(emb_df['quantity'], errors='coerce')
                
                # Remove any rows with invalid numeric data
                emb_df = emb_df.dropna(subset=['total', 'quantity'])
                
                if emb_df.empty:
                    return {
                        'no_data': True,
                        'stats': [],
                        'charts': {},
                        'peak_embellishment': 'No valid embellishment data',
                        'embellishment_usage_rate': 0,
                        'avg_embellishment_revenue': 0
                    }
                
                emb_stats = emb_df.groupby('embellishment').agg({
                    'total': ['sum', 'mean', 'count'],
                    'quantity': 'sum'
                }).round(2)
                
                emb_stats.columns = ['total_revenue', 'avg_sale', 'usage_count', 'total_quantity']
                emb_stats = emb_stats.reset_index()
                
                # Calculate usage rate for each embellishment
                total_sales = len(df)
                emb_stats['usage_rate'] = (emb_stats['usage_count'] / total_sales * 100) if total_sales > 0 else 0
                
                charts = {}
                
                try:
                    # 1. Top Embellishments (Bar Chart)
                    if len(emb_stats) > 0:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        top_embs = emb_stats.nlargest(min(10, len(emb_stats)), 'total_revenue')
                        if len(top_embs) > 0:
                            sns.barplot(data=top_embs, x='total_revenue', y='embellishment', ax=ax)
                            ax.set_title('Top Embellishments by Revenue')
                            ax.set_xlabel('Revenue ($)')
                            plt.tight_layout()
                            charts['embellishment_revenue'] = self._create_chart(fig, 'Top Embellishments')
                            plt.close(fig)
                    
                    # 2. Embellishment Usage Frequency
                    if len(emb_stats) > 0:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        usage_top = emb_stats.nlargest(min(10, len(emb_stats)), 'usage_count')
                        if len(usage_top) > 0:
                            sns.barplot(data=usage_top, x='usage_count', y='embellishment', ax=ax)
                            ax.set_title('Most Used Embellishments')
                            ax.set_xlabel('Number of Uses')
                            plt.tight_layout()
                            charts['embellishment_usage'] = self._create_chart(fig, 'Embellishment Usage')
                            plt.close(fig)
                    
                    # 3. Embellishment Revenue vs Usage Scatter
                    if len(emb_stats) > 1:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.scatterplot(data=emb_stats, x='usage_count', y='total_revenue', 
                                      size='avg_sale', sizes=(50, 300), ax=ax, legend=False)
                        ax.set_title('Embellishment Performance: Usage vs Revenue')
                        ax.set_xlabel('Usage Count')
                        ax.set_ylabel('Total Revenue ($)')
                        plt.tight_layout()
                        charts['embellishment_scatter'] = self._create_chart(fig, 'Embellishment Scatter')
                        plt.close(fig)
                except Exception as e:
                    print(f"Error creating embellishment charts: {e}")
                    charts = {}
                
                # Calculate overall embellishment metrics
                total_sales_with_emb = len(emb_df)
                total_sales = len(df)
                embellishment_usage_rate = (total_sales_with_emb / total_sales * 100) if total_sales > 0 else 0
                avg_embellishment_revenue = emb_stats['total_revenue'].mean() if len(emb_stats) > 0 else 0
                peak_embellishment = emb_stats.loc[emb_stats['total_revenue'].idxmax(), 'embellishment'] if len(emb_stats) > 0 else 'None'
                
                return {
                    'stats': emb_stats.to_dict('records'),
                    'charts': charts,
                    'peak_embellishment': peak_embellishment,
                    'embellishment_usage_rate': embellishment_usage_rate,
                    'avg_embellishment_revenue': avg_embellishment_revenue
                }
                
            except Exception as e:
                print(f"Error processing embellishment data: {e}")
                return {
                    'no_data': True,
                    'stats': [],
                    'charts': {},
                    'peak_embellishment': 'Error processing data',
                    'embellishment_usage_rate': 0,
                    'avg_embellishment_revenue': 0
                }
                
        except Exception as e:
            print(f"Error in get_embellishment_analytics: {e}")
            return {
                'no_data': True,
                'stats': [],
                'charts': {},
                'peak_embellishment': 'Error processing data',
                'embellishment_usage_rate': 0,
                'avg_embellishment_revenue': 0
            }
    
    # DAY OF WEEK ANALYTICS
    def get_day_analytics(self, df):
        """Get analytics for days of the week"""
        if df.empty:
            return None
        
        # Group by day of week and calculate metrics
        df['day_of_week'] = pd.to_datetime(df['sale_date']).dt.day_name()
        day_stats = df.groupby('day_of_week').agg({
            'total_amount': ['sum', 'count', 'mean'],
            'transaction_id': 'nunique'
        }).reset_index()
        
        # Rename columns for clarity
        day_stats.columns = ['day_of_week', 'total_revenue', 'total_items', 'avg_sale', 'transaction_count']
        
        # Sort by day of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_stats['day_of_week'] = pd.Categorical(day_stats['day_of_week'], categories=day_order, ordered=True)
        day_stats = day_stats.sort_values('day_of_week')
        
        # Convert to list of dicts for template
        stats = day_stats.to_dict('records')
        
        return {
            'stats': stats,
            'peak_day': day_stats.loc[day_stats['total_revenue'].idxmax(), 'day_of_week'] if not day_stats.empty else None,
            'avg_daily_revenue': day_stats['total_revenue'].mean() if not day_stats.empty else 0
        }
    
    # MONTHLY ANALYTICS
    def get_monthly_analytics(self, df):
        """Get analytics for months"""
        if df.empty:
            return None
        
        # Group by month and calculate metrics
        df['month'] = pd.to_datetime(df['sale_date']).dt.strftime('%B %Y')
        month_stats = df.groupby('month').agg({
            'total_amount': ['sum', 'count', 'mean'],
            'transaction_id': 'nunique'
        }).reset_index()
        
        # Rename columns for clarity
        month_stats.columns = ['month', 'total_revenue', 'total_items', 'avg_sale', 'transaction_count']
        
        # Sort by date
        month_stats['sort_date'] = pd.to_datetime(month_stats['month'])
        month_stats = month_stats.sort_values('sort_date')
        month_stats = month_stats.drop('sort_date', axis=1)
        
        # Calculate month-over-month growth
        month_stats['growth'] = month_stats['total_revenue'].pct_change() * 100
        
        # Convert to list of dicts for template
        stats = month_stats.to_dict('records')
        
        return {
            'stats': stats,
            'peak_month': month_stats.loc[month_stats['total_revenue'].idxmax(), 'month'] if not month_stats.empty else None,
            'avg_monthly_revenue': month_stats['total_revenue'].mean() if not month_stats.empty else 0
        }
    
    # DASHBOARD SUMMARY
    def get_dashboard_summary(self, df):
        """Get key metrics for dashboard"""
        # Initialize default values
        default_metrics = {
            'total_revenue': 0.0,
            'total_transactions': 0,
            'avg_transaction': 0.0,
            'today_sales': 0.0,
            'today_transactions': 0,
            'this_month_sales': 0.0,
            'top_product': "No products",
            'top_store': "No stores",
            'daily_change': 0.0,
            'weekly_change': 0.0,
            'yesterday_sales': 0.0,
            'this_week_sales': 0.0
        }
        
        if df.empty:
            return default_metrics
        
        try:
            # Convert dates to pandas datetime for consistent comparison
            today = pd.Timestamp.now().normalize()
            yesterday = today - pd.Timedelta(days=1)
            this_week_start = today - pd.Timedelta(days=today.weekday())
            last_week_start = this_week_start - pd.Timedelta(days=7)
            this_month_start = today.replace(day=1)
            
            # Convert sale_date to datetime for filtering
            df['sale_date'] = pd.to_datetime(df['sale_date'])
            
            # Calculate key metrics - simplified calculations
            total_revenue = float(df['total'].sum())
            total_transactions = len(df)
            avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0.0
            
            # Today's metrics
            today_df = df[df['sale_date'].dt.normalize() == today]
            today_sales = float(today_df['total'].sum())
            today_transactions = len(today_df)
            
            # Yesterday's metrics
            yesterday_df = df[df['sale_date'].dt.normalize() == yesterday]
            yesterday_sales = float(yesterday_df['total'].sum())
            
            # This week's metrics
            this_week_df = df[df['sale_date'].dt.normalize() >= this_week_start]
            this_week_sales = float(this_week_df['total'].sum())
            
            # Last week's metrics
            last_week_df = df[(df['sale_date'].dt.normalize() >= last_week_start) & 
                             (df['sale_date'].dt.normalize() < this_week_start)]
            last_week_sales = float(last_week_df['total'].sum())
            
            # This month's metrics
            this_month_df = df[df['sale_date'].dt.normalize() >= this_month_start]
            this_month_sales = float(this_month_df['total'].sum())
            
            # Calculate percentage changes - simplified
            daily_change = ((today_sales - yesterday_sales) / yesterday_sales * 100) if yesterday_sales > 0 else 0.0
            weekly_change = ((this_week_sales - last_week_sales) / last_week_sales * 100) if last_week_sales > 0 else 0.0
            
            # Get top performers - simplified
            try:
                top_product = df.groupby('product_name')['total'].sum().idxmax()
            except (ValueError, KeyError):
                top_product = "No products"
                
            try:
                top_store = df.groupby('store_name')['total'].sum().idxmax()
            except (ValueError, KeyError):
                top_store = "No stores"
            
            return {
                'total_revenue': round(total_revenue, 2),
                'total_transactions': total_transactions,
                'avg_transaction': round(avg_transaction, 2),
                'today_sales': round(today_sales, 2),
                'today_transactions': today_transactions,
                'this_month_sales': round(this_month_sales, 2),
                'yesterday_sales': round(yesterday_sales, 2),
                'this_week_sales': round(this_week_sales, 2),
                'top_product': top_product,
                'top_store': top_store,
                'daily_change': round(daily_change, 1),
                'weekly_change': round(weekly_change, 1)
            }
        except Exception as e:
            print(f"Error in get_dashboard_summary: {str(e)}")
            return default_metrics
    
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
        
        # Function to get best and worst without overlap
        def get_best_worst(series, best_count=5, worst_count=5):
            if len(series) <= best_count + worst_count:
                # If total items <= sum of best + worst counts, split them
                mid_point = len(series) // 2
                if mid_point == 0:
                    # Only one item, put it in best
                    return series.to_dict(), {}
                best = series.head(mid_point)
                worst = series.tail(len(series) - mid_point)
            else:
                # Enough items for separate best and worst
                best = series.head(best_count)
                worst = series.tail(worst_count)
            
            return best.to_dict(), worst.to_dict()
        
        # Apply safe best/worst logic
        best_products, worst_products = get_best_worst(product_performance, 10, 10)
        best_categories, worst_categories = get_best_worst(category_performance, 5, 5)
        best_stores, worst_stores = get_best_worst(store_performance, 10, 10)
        
        if not embellishment_performance.empty:
            best_embellishments, worst_embellishments = get_best_worst(embellishment_performance, 10, 10)
        else:
            best_embellishments, worst_embellishments = {}, {}
        
        best_days, worst_days = get_best_worst(day_performance, 3, 3)  # At most 7 days
        
        return {
            'best_products': best_products,
            'worst_products': worst_products,
            'best_categories': best_categories,
            'worst_categories': worst_categories,
            'best_stores': best_stores,
            'worst_stores': worst_stores,
            'best_embellishments': best_embellishments,
            'worst_embellishments': worst_embellishments,
            'best_days': best_days,
            'worst_days': worst_days
        }