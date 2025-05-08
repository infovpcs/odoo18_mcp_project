#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for importing product data with update functionality.
"""
import os
import sys
import csv
import tempfile
from direct_export_import import import_records

def main():
    # Create a temporary CSV file with the product data
    temp_file = '/tmp/import.csv'
    
    # Use the CSV content from the user's message
    csv_content = """id,standard_price,is_favorite,default_code,name,lst_price,product_template_variant_value_ids,categ_id,type,uom_po_id,purchase_line_warn,sale_line_warn,tracking,uom_id,service_tracking,product_variant_ids,product_tmpl_id
product.product_product_5,600.0,,E-COMVPCS06,Corner Desk Right Sit,150,,All / Saleable / Office Furniture,consu,Units,no-message,no-message,none,Units,no,[E-COM06] Corner Desk Right Sit,5
product.product_product_6,800.0,,E-COMVPCS07,Large Cabinet,500,,All / Saleable / Office Furniture,consu,Units,no-message,no-message,none,Units,no,[E-COM07] Large Cabinet,6
product.product_product_7,1000,,E-COMVPCS08,Storage Box,250,,All / Saleable / Office Furniture,consu,Units,no-message,no-message,none,Units,no,[E-COM08] Storage Box,7
product.product_product_8,1299.0,,E-COMVPCS09,Large Desk,2000,,All / Saleable / Office Furniture,consu,Units,no-message,no-message,none,Units,no,[E-COM09] Large Desk,8
product.product_product_9,1000,,E-COMVPCS10,Pedal Bin,47.0,,All / Saleable / Office Furniture,consu,Units,no-message,no-message,none,Units,no,[E-COM10] Pedal Bin,9
product.product_product_10,120.5,,E-COMVPCS11,Cabinet with Doors,140.0,,All / Saleable / Office Furniture,consu,Units,no-message,no-message,none,Units,no,[E-COM11] Cabinet with Doors,10
product.product_product_11,140,,E-COMVPCS12,Conference Chair,150,Legs: Steel,All / Saleable / Office Furniture,consu,Units,no-message,no-message,none,Units,no,[E-COM12] Conference Chair (Steel),11
product.product_product_11b,150,,E-COMVPCS13,Conference Chair,50,Legs: Aluminium,All / Saleable / Office Furniture,consu,Units,no-message,no-message,none,Units,no,[E-COM12] Conference Chair (Steel),11"""
    
    # Write the CSV content to the temporary file
    with open(temp_file, 'w') as f:
        f.write(csv_content)
    
    print(f"Created temporary CSV file at {temp_file}")
    
    # Import the products with update_if_exists=True
    result = import_records(
        input_path=temp_file,
        model_name='product.product',
        create_if_not_exists=True,
        update_if_exists=True,
        force=True  # Force import even if required fields are missing
    )
    
    # Print the result
    print("\nImport Result:")
    print(f"Success: {result['success']}")
    if not result['success']:
        print(f"Error: {result['error']}")
    print(f"Created: {result['imported_records']}")
    print(f"Updated: {result['updated_records']}")
    print(f"Failed: {result['failed_records']}")
    print(f"Total records in CSV: {result['total_records']}")
    
    # Clean up
    # os.remove(temp_file)
    # print(f"Removed temporary file {temp_file}")

if __name__ == '__main__':
    main()
