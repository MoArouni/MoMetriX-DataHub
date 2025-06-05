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
                sale.store.name if sale.store else 'Unknown Store',
                sale.product.category.name if sale.product and sale.product.category else 'Unknown Category',
                sale.product.name if sale.product else 'Unknown Product',
                str(sale.quantity),
                f"{sale.total_amount:.2f}",
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
        
        # Validate headers
        expected_headers = set(self.CSV_HEADERS)
        actual_headers = set(csv_reader.fieldnames or [])
        
        if not expected_headers.issubset(actual_headers):
            missing_headers = expected_headers - actual_headers
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
    
    def _create_sale_from_row(self, row: Dict[str, str], user_id: int, row_num: int) -> Sale:
        """
        Create a Sale object from a CSV row
        
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
        
        # Get or create store
        store_name = row['store_name'].strip()
        if not store_name:
            raise ValueError("store_name cannot be empty")
        
        store = Store.query.filter_by(
            name=store_name, 
            company_id=self.company_id
        ).first()
        
        if not store:
            # Auto-create store if it doesn't exist
            store = Store(
                name=store_name,
                company_id=self.company_id
            )
            db.session.add(store)
            db.session.flush()  # Get the ID without committing
        
        # Get or create product category
        category_name = row['product_category'].strip()
        if not category_name:
            raise ValueError("product_category cannot be empty")
        
        category = ProductCategory.query.filter_by(
            name=category_name,
            company_id=self.company_id
        ).first()
        
        if not category:
            # Auto-create category if it doesn't exist
            category = ProductCategory(
                name=category_name,
                company_id=self.company_id
            )
            db.session.add(category)
            db.session.flush()  # Get the ID without committing
        
        # Get or create product
        product_name = row['product_name'].strip()
        if not product_name:
            raise ValueError("product_name cannot be empty")
        
        product = Product.query.filter_by(
            name=product_name,
            category_id=category.id,
            company_id=self.company_id
        ).first()
        
        if not product:
            # Auto-create product if it doesn't exist
            # Extract base price from total if available
            try:
                total_amount = Decimal(row['total'].strip())
                quantity = int(row['quantity'].strip())
                base_price = total_amount / quantity if quantity > 0 else total_amount
            except (ValueError, ZeroDivisionError):
                base_price = Decimal('0.00')
            
            product = Product(
                name=product_name,
                category_id=category.id,
                company_id=self.company_id,
                base_price=base_price
            )
            db.session.add(product)
            db.session.flush()  # Get the ID without committing
        
        # Parse numeric fields
        try:
            quantity = int(row['quantity'].strip())
            if quantity <= 0:
                raise ValueError("quantity must be positive")
        except ValueError:
            raise ValueError(f"Invalid quantity: {row['quantity']}")
        
        try:
            card_amount = Decimal(row['card_amount'].strip()) if row['card_amount'].strip() else Decimal('0.00')
        except ValueError:
            raise ValueError(f"Invalid card_amount: {row['card_amount']}")
        
        try:
            cash_amount = Decimal(row['cash_amount'].strip()) if row['cash_amount'].strip() else Decimal('0.00')
        except ValueError:
            raise ValueError(f"Invalid cash_amount: {row['cash_amount']}")
        
        # Validate that total matches card + cash amounts
        try:
            total_from_csv = Decimal(row['total'].strip())
            calculated_total = card_amount + cash_amount
            
            # Allow small discrepancy due to rounding
            if abs(total_from_csv - calculated_total) > Decimal('0.01'):
                current_app.logger.warning(
                    f"Row {row_num}: Total amount mismatch. "
                    f"CSV total: {total_from_csv}, Calculated: {calculated_total}"
                )
        except ValueError:
            raise ValueError(f"Invalid total amount: {row['total']}")
        
        # Create sale object
        sale = Sale(
            company_id=self.company_id,
            user_id=user_id,
            store_id=store.id,
            product_id=product.id,
            sale_date=sale_date,
            quantity=quantity,
            card_amount=card_amount,
            cash_amount=cash_amount,
            notes=row['notes'].strip() if row['notes'] else None
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
            
            # Validate headers
            expected_headers = set(self.CSV_HEADERS)
            actual_headers = set(csv_reader.fieldnames or [])
            
            if not expected_headers.issubset(actual_headers):
                missing_headers = expected_headers - actual_headers
                error_messages.append(f"Missing required headers: {', '.join(missing_headers)}")
            
            # Check if there are any data rows
            row_count = 0
            for row_num, row in enumerate(csv_reader, start=2):
                row_count += 1
                
                # Basic validation on first few rows
                if row_count <= 5:  # Only validate first 5 rows for performance
                    if not row['sale_date'].strip():
                        error_messages.append(f"Row {row_num}: sale_date cannot be empty")
                    if not row['store_name'].strip():
                        error_messages.append(f"Row {row_num}: store_name cannot be empty")
                    if not row['product_category'].strip():
                        error_messages.append(f"Row {row_num}: product_category cannot be empty")
                    if not row['product_name'].strip():
                        error_messages.append(f"Row {row_num}: product_name cannot be empty")
            
            if row_count == 0:
                error_messages.append("CSV file contains no data rows")
                
        except Exception as e:
            error_messages.append(f"CSV parsing error: {str(e)}")
        
        return len(error_messages) == 0, error_messages 