import pandas as pd
from django.core.management.base import BaseCommand
from delivery_stock.models import SuplierSKU

class Command(BaseCommand):
    help = "Command to create Supplier SKUs"
    
    def handle(self, *args, **options):
        # Get current supplier SKUs to avoid duplicates
        current_sku = list(SuplierSKU.objects.all().values_list("barcode", flat=True))

        # Read the Excel file using pandas (make sure to install openpyxl)
        df = pd.read_excel("supplier_sku.xlsx", engine='openpyxl')

        # Sanitize column names
        df.columns = df.columns.str.strip().str.lower()  # Clean up spaces and case differences

        # Print the columns to verify they are correct
        print(df.columns)

        # Use a set to track barcodes that have been processed
        seen_barcodes = set()

        loc_inst = []
        for index, row in df.iterrows():
            # Ensure the 'barcode' exists in the row, else skip the row
            if 'barcode' not in row or pd.isna(row['barcode']):
                continue

            barcode = str(row['barcode'])  # Assuming the column name is 'barcode'

            # Only add if barcode is unique and not already in the current SKUs
            if barcode not in current_sku and barcode not in seen_barcodes:
                seen_barcodes.add(barcode)  # Mark the barcode as processed
                loc_inst.append(
                    SuplierSKU(
                        barcode=barcode,
                        sku=int(row['sku']),  # Assuming the column name is 'sku'
                        deskription=str(row['deskription'])  # Assuming the column name is 'deskription'
                    )
                )

        # Bulk create all unique SupplierSKUs
        SuplierSKU.objects.bulk_create(loc_inst)

        self.stdout.write("SupplierSKUs were created successfully")
