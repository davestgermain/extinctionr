Prerequisites:
Python 3.8


```
# In a new directory:

python -m venv venv

# Activate the virtual environment
source ./venv/bin/activate

git clone <this project>
cd extinctionr

pip install django
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Note: to exit the python venv use:

`deactivate`


