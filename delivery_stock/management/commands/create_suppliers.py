from django.core.management.base import BaseCommand
from delivery_stock.models import Supplier
import xlrd


class Command(BaseCommand):
    help = "Command to create Supplier"

    def handle(self, *args, **options):
        workbook = xlrd.open_workbook("suppliers.xls")
        sheet = workbook.sheet_by_index(0)

        supp_inst = [
            Supplier(
                name=str(sheet.row_values(row)[1]),
                supplier_wms_id=str(sheet.row_values(row)[0]),
            )
            for row in range(1, sheet.nrows)
        ]
        Supplier.objects.bulk_create(supp_inst)

        self.stdout.write("Suppliers create successful")
