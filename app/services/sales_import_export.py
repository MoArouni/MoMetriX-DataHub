"""
Sales Import/Export Service
Handles importing and exporting sales data in CSV format
"""

import csv
import io
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from flask import current_app
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.sales import Sale
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.store import Store
from app.models.user import User
from app.models.company import Company


class SalesImportExportService:
    """Service for handling sales data import and export"""
    
    # CSV header structure based on the converted data
    CSV_HEADERS = [
        'sale_date',
        'store_name', 
        'product_category',
        'product_name',
        'quantity',
        'total',
        'card_amount',
        'cash_amount',
        'notes'
    ]
    
    def __init__(self, company_id: int):
        self.company_id = company_id
        self.company = Company.query.get(company_id)
        if not self.company:
            raise ValueError(f"Company with ID {company_id} not found")
    
    def export_sales_to_csv(self, start_date: Optional[date] = None, 
                           end_date: Optional[date] = None) -> str:
        """
        Export sales data to CSV format
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            CSV string with sales data
        """
        # Build query
        query = Sale.query.filter_by(company_id=self.company_id)
        
        if start_date:
            query = query.filter(Sale.sale_date >= start_date)
        if end_date:
            query = query.filter(Sale.sale_date <= end_date)
            
        sales = query.order_by(Sale.sale_date.desc()).all()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(self.CSV_HEADERS)
        
        # Write data rows
        for sale in sales:
            row = [
                sale.sale_date.strftime('%Y-%m-%d'),
                sale.store_name if hasattr(sale, 'store_name') and sale.store_name else (sale.store.name if sale.store else 'Unknown Store'),
                sale.product_category if hasattr(sale, 'product_category') and sale.product_category else (sale.product.category.name if sale.product and sale.product.category else 'Unknown Category'),
                sale.product_name if hasattr(sale, 'product_name') and sale.product_name else (sale.product.name if sale.product else 'Unknown Product'),
                str(sale.quantity),
                f"{sale.total:.2f}" if hasattr(sale, 'total') and sale.total else f"{sale.total_amount:.2f}",
                f"{sale.card_amount:.2f}",
                f"{sale.cash_amount:.2f}",
                sale.notes or ''
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def import_sales_from_csv(self, csv_content: str, user_id: int) -> Tuple[int, int, List[str]]:
        """
        Import sales data from CSV content
        
        Args:
            csv_content: CSV content as string
            user_id: ID of the user performing the import
            
        Returns:
            Tuple of (successful_imports, failed_imports, error_messages)
        """
        successful_imports = 0
        failed_imports = 0
        error_messages = []
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Validate headers - only require essential ones
        required_headers = {'sale_date'}  # Only sale_date is truly required
        actual_headers = set(csv_reader.fieldnames or [])
        
        if not required_headers.issubset(actual_headers):
            missing_headers = required_headers - actual_headers
            error_messages.append(f"Missing required headers: {', '.join(missing_headers)}")
            return 0, 0, error_messages
        
        # Process each row
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 since row 1 is header
            try:
                sale = self._create_sale_from_row(row, user_id, row_num)
                if sale:
                    db.session.add(sale)
                    successful_imports += 1
            except Exception as e:
                failed_imports += 1
                error_messages.append(f"Row {row_num}: {str(e)}")
                current_app.logger.error(f"Import error on row {row_num}: {str(e)}")
        
        # Commit successful imports
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            error_messages.append(f"Database error during commit: {str(e)}")
            return 0, successful_imports + failed_imports, error_messages
        
        return successful_imports, failed_imports, error_messages
    
    def import_sales_with_progress(self, csv_content: str, user_id: int, progress_callback=None) -> Tuple[int, int, List[str]]:
        """
        Import sales data from CSV content with progress tracking
        
        Args:
            csv_content: CSV content as string
            user_id: ID of the user performing the import
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (successful_imports, failed_imports, error_messages)
        """
        successful_imports = 0
        failed_imports = 0
        error_messages = []
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Validate headers - only require essential ones
        required_headers = {'sale_date'}  # Only sale_date is truly required
        actual_headers = set(csv_reader.fieldnames or [])
        
        if not required_headers.issubset(actual_headers):
            missing_headers = required_headers - actual_headers
            error_messages.append(f"Missing required headers: {', '.join(missing_headers)}")
            return 0, 0, error_messages
        
        # Count total rows first for progress calculation
        rows = list(csv_reader)
        total_rows = len(rows)
        
        if total_rows == 0:
            error_messages.append("No data rows found in CSV")
            return 0, 0, error_messages
        
        # Process each row with progress tracking
        batch_size = 50  # Process in batches for better performance
        processed_count = 0
        
        for i, row in enumerate(rows):
            row_num = i + 2  # Start at 2 since row 1 is header
            
            try:
                sale = self._create_sale_from_row(row, user_id, row_num)
                if sale:
                    db.session.add(sale)
                    successful_imports += 1
                    
                    # Commit in batches
                    if (i + 1) % batch_size == 0:
                        try:
                            db.session.commit()
                        except IntegrityError as e:
                            db.session.rollback()
                            error_messages.append(f"Database error in batch ending at row {row_num}: {str(e)}")
                            # Continue with next batch
                            
            except Exception as e:
                failed_imports += 1
                error_messages.append(f"Row {row_num}: {str(e)}")
                current_app.logger.error(f"Import error on row {row_num}: {str(e)}")
            
            processed_count += 1
            
            # Update progress if callback provided
            if progress_callback:
                progress = int((processed_count / total_rows) * 100)
                status = f"Processing sales data... ({processed_count}/{total_rows})"
                detail = f"Imported {successful_imports} records, {failed_imports} failed"
                progress_callback(progress, status, detail)
        
        # Final commit for remaining records
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            error_messages.append(f"Database error during final commit: {str(e)}")
        
        return successful_imports, failed_imports, error_messages
    
    def _create_sale_from_row(self, row: Dict[str, str], user_id: int, row_num: int) -> Sale:
        """
        Create a Sale object from a CSV row - automatically creates missing stores, categories, and products
        
        Args:
            row: Dictionary representing a CSV row
            user_id: ID of the user performing the import
            row_num: Row number for error reporting
            
        Returns:
            Sale object ready to be saved
        """
        # Parse and validate sale_date
        try:
            sale_date = datetime.strptime(row['sale_date'].strip(), '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"Invalid date format in sale_date: {row['sale_date']}")
        
        # Handle missing values with defaults
        store_name = row.get('store_name', '').strip() or 'Default Store'
        product_category = row.get('product_category', '').strip() or 'General'
        product_name = row.get('product_name', '').strip() or 'Unknown Product'
        
        # Parse numeric fields with defaults
        try:
            quantity = int(row.get('quantity', '1').strip()) if row.get('quantity', '').strip() else 1
            if quantity <= 0:
                quantity = 1
        except ValueError:
            quantity = 1
        
        try:
            total = Decimal(row.get('total', '0').strip()) if row.get('total', '').strip() else Decimal('0.00')
            if total < 0:
                total = Decimal('0.00')
        except ValueError:
            total = Decimal('0.00')
        
        try:
            card_amount = Decimal(row.get('card_amount', '0').strip()) if row.get('card_amount', '').strip() else Decimal('0.00')
            if card_amount < 0:
                card_amount = Decimal('0.00')
        except ValueError:
            card_amount = Decimal('0.00')
        
        try:
            cash_amount = Decimal(row.get('cash_amount', '0').strip()) if row.get('cash_amount', '').strip() else Decimal('0.00')
            if cash_amount < 0:
                cash_amount = Decimal('0.00')
        except ValueError:
            cash_amount = Decimal('0.00')
        
        # If total is 0 but we have card/cash amounts, calculate total
        if total == 0 and (card_amount > 0 or cash_amount > 0):
            total = card_amount + cash_amount
        
        # If total is provided but card/cash don't add up, adjust cash amount
        calculated_total = card_amount + cash_amount
        if total > 0 and abs(calculated_total - total) > Decimal('0.01'):
            # Adjust cash amount to make totals match
            cash_amount = total - card_amount
            if cash_amount < 0:
                card_amount = total
                cash_amount = Decimal('0.00')
        
        notes = row.get('notes', '').strip()
        
        # Auto-create store if it doesn't exist
        store = Store.query.filter_by(company_id=self.company_id, name=store_name).first()
        if not store:
            store = Store(
                company_id=self.company_id,
                name=store_name,
                location='Auto-created during import'
            )
            db.session.add(store)
            db.session.flush()  # Get the ID
        
        # Auto-create category if it doesn't exist
        category = ProductCategory.query.filter_by(company_id=self.company_id, name=product_category).first()
        if not category:
            category = ProductCategory(
                company_id=self.company_id,
                name=product_category
            )
            db.session.add(category)
            db.session.flush()  # Get the ID
        
        # Auto-create product if it doesn't exist
        product = Product.query.filter_by(
            company_id=self.company_id, 
            name=product_name, 
            category_id=category.id
        ).first()
        if not product:
            # Calculate base price per unit
            base_price = total / quantity if quantity > 0 else total
            product = Product(
                company_id=self.company_id,
                name=product_name,
                category_id=category.id,
                base_price=base_price  # Use the per-unit price as base price
            )
            db.session.add(product)
            db.session.flush()  # Get the ID
        
        # Create the sale object with both direct CSV data and linked entities
        sale = Sale(
            company_id=self.company_id,
            user_id=user_id,
            sale_date=sale_date,
            store_id=store.id,
            store_name=store_name,
            product_id=product.id,
            product_category=product_category,
            product_name=product_name,
            quantity=quantity,
            total=total,
            card_amount=card_amount,
            cash_amount=cash_amount,
            notes=notes
        )
        
        return sale
    
    def validate_csv_format(self, csv_content: str) -> Tuple[bool, List[str]]:
        """
        Validate CSV format without importing
        
        Args:
            csv_content: CSV content as string
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        error_messages = []
        
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Validate headers - only require essential ones
            required_headers = {'sale_date'}  # Only sale_date is truly required
            actual_headers = set(csv_reader.fieldnames or [])
            
            if not required_headers.issubset(actual_headers):
                missing_headers = required_headers - actual_headers
                error_messages.append(f"Missing required headers: {', '.join(missing_headers)}")
            
            # Check if there are any data rows
            row_count = 0
            for row_num, row in enumerate(csv_reader, start=2):
                row_count += 1
                
                # Basic validation on first few rows - only check essential fields
                if row_count <= 5:  # Only validate first 5 rows for performance
                    if not row.get('sale_date', '').strip():
                        error_messages.append(f"Row {row_num}: sale_date cannot be empty")
            
            if row_count == 0:
                error_messages.append("CSV file contains no data rows")
                
        except Exception as e:
            error_messages.append(f"CSV parsing error: {str(e)}")
        
        return len(error_messages) == 0, error_messages 