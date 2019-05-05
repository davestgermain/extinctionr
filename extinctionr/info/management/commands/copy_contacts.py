from django.core.management.base import BaseCommand, CommandError
import csv
from extinctionr.utils import get_contact
from contacts.models import Contact

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)

    def handle(self, *args, **kwargs):
        first = True
        with open(kwargs['filename'], 'r') as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                # if first:
                #     first = False
                #     continue
                first_name = row['first_name']
                last_name = row['last_name']
                email = row['email']
                zipcode = row['zip_code']
                city = row['can2_user_city']
                if email:
                    c = get_contact(email, first_name=first_name, last_name=last_name, postcode=zipcode, city=city)
                    self.stdout.write(str(c))
