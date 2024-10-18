from django.core.management.base import BaseCommand
from delivery_stock.models import ReasoneComment
import xlrd


class Command(BaseCommand):
    help = "Auto create Reason code"

    def handle(self, *args, **options):
        workbook = xlrd.open_workbook("reasons.xls")
        sheet = workbook.sheet_by_index(0)
        existing_reasons = [(item.name, item.reception) for item in ReasoneComment.objects.all()]

        new_reasons = [
            ReasoneComment(name=sheet.row_values(row)[0], reception=sheet.row_values(row)[1])
            for row in range(sheet.nrows)
            if (sheet.row_values(row)[0], sheet.row_values(row)[1]) not in existing_reasons
        ]
        
        ReasoneComment.objects.bulk_create(new_reasons)

        self.stdout.write("Reasons created successfully")
