from django.core.management.base import BaseCommand
from delivery_stock.models import Location
import xlrd

class Command(BaseCommand):
    help = "Command to create Locations"
    
    def handle(self, *args, **options):
        current_loc = list(Location.objects.all().values_list("name", flat=True))
        
        workbook = xlrd.open_workbook("locations.xls")
        sheet = workbook.sheet_by_index(0)

        loc_inst = [
            Location(
                name = str(sheet.row_values(row)[0]),
                work_zone = int(sheet.row_values(row)[1])
            )
            for row in range(1, sheet.nrows) 
            if str(sheet.row_values(row)[0]) not in current_loc
        ]
        Location.objects.bulk_create(loc_inst)

        self.stdout.write("Locations was created")

        