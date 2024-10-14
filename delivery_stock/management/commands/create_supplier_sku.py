from django.core.management.base import BaseCommand
from delivery_stock.models import SuplierSKU
import xlrd

class Command(BaseCommand):
    help = "Command to create Locations"
    
    def handle(self, *args, **options):
        current_loc = list(SuplierSKU.objects.all().values_list("barcode", flat=True))
        
        workbook = xlrd.open_workbook("supplier_sku.xls")
        sheet = workbook.sheet_by_index(0)

        loc_inst = [
            SuplierSKU(
                barcode = str(sheet.row_values(row)[0]),
                sku = int(sheet.row_values(row)[1]),
                deskription = str(sheet.row_values(row)[2])
            )
            for row in range(1, sheet.nrows) 
            if str(sheet.row_values(row)[0]) not in current_loc
        ][:500] #remove slice for list
        SuplierSKU.objects.bulk_create(loc_inst)

        self.stdout.write("SupplierSKU was created")

        