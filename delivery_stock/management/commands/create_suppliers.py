from django.core.management.base import BaseCommand
from delivery_stock.models import Supplier
import xlrd

class Command(BaseCommand):
    help = "Command to create Supplier"

    def handle(self, *args, **options):
        workbook = xlrd.open_workbook("suppliers.xls")
        sheet = workbook.sheet_by_index(0)

        # Fetch all existing supplier WMS IDs to avoid duplicates
        existing_suppliers = set(Supplier.objects.values_list('supplier_wms_id', flat=True))

        # Create a list of Supplier instances for suppliers that don't already exist
        supp_inst = [
            Supplier(
                name=str(sheet.row_values(row)[1]),
                supplier_wms_id=str(sheet.row_values(row)[0])
            )
            for row in range(1, sheet.nrows)
            if str(sheet.row_values(row)[0]) not in existing_suppliers
        ]

        # Bulk create the new suppliers
        if supp_inst:
            Supplier.objects.bulk_create(supp_inst)

        self.stdout.write("Suppliers creation successful")
