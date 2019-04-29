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
            reader = csv.reader(fp)
            for row in reader:
                if first:
                    first = False
                    continue
                name = row[0].split(' ', 1)
                notes = row[1]
                email = row[2].lower()
                phone = row[3].replace('(', '').replace(')', '')
                group = row[4]
                if len(name) == 2:
                    first_name, last_name = name
                elif len(name) == 1:
                    first_name = name[0]
                    last_name = ''
                else:
                    first_name = last_name = ''
                if email:
                    c = get_contact(email, first_name=first_name, last_name=last_name, phone=phone, description=notes)
                    self.stdout.write(str(c))
