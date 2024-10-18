from django.core.management.base import BaseCommand
from delivery_stock.models import SuplierSKU
import xlrd

class Command(BaseCommand):
    help = "Command to create Supplier SKUs"
    
    def handle(self, *args, **options):
        # Get current supplier SKUs to avoid duplicates
        current_sku = list(SuplierSKU.objects.all().values_list("barcode", flat=True))

        # Open the Excel workbook
        workbook = xlrd.open_workbook("supplier_sku.xls")
        sheet = workbook.sheet_by_index(0)

        # Use a set to track barcodes that have been processed
        seen_barcodes = set()

        loc_inst = []
        for row in range(1, sheet.nrows):
            barcode = str(sheet.row_values(row)[0])

            # Only add if barcode is unique and not already in the current SKUs
            if barcode not in current_sku and barcode not in seen_barcodes:
                seen_barcodes.add(barcode)  # Mark the barcode as processed
                loc_inst.append(
                    SuplierSKU(
                        barcode=barcode,
                        sku=int(sheet.row_values(row)[1]),
                        deskription=str(sheet.row_values(row)[2])
                    )
                )

        # Bulk create all unique SupplierSKUs
        SuplierSKU.objects.bulk_create(loc_inst)

        self.stdout.write("SupplierSKUs were created successfully")
