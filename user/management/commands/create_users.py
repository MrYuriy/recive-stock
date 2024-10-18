from django.core.management.base import BaseCommand
from user.models import User
import xlrd

class Command(BaseCommand):
    help = "Auto create Users"

    def handle(self, *args, **options):
        currnt_user = list(User.objects.all()\
                           .values_list("username", flat=True))

        workbook = xlrd.open_workbook("users.xls")
        sheet = workbook.sheet_by_index(0)

        user_list = [
            User(
                full_name=str(sheet.row_values(row)[0]),
                username=str(sheet.row_values(row)[1]),
                role=str(sheet.row_values(row)[2]),
            )
            for row in range(1, sheet.nrows)
            if str(sheet.row_values(row)[0]) not in currnt_user
        ]

        for user in user_list:
            user.set_password("123")

        User.objects.bulk_create(user_list)

        self.stdout.write("Users was created")