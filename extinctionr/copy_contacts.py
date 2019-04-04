import csv
import sys
from contacts.models import Contact

with open(sys.argv[1], 'rb') as fp:
	reader = csv.reader(fp)
	for row in reader:
		print(row)

