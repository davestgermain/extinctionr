# Generated by Django 3.0.6 on 2020-06-02 21:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0010_specialnotice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specialnotice',
            name='enabled',
            field=models.BooleanField(default=False, help_text='Turn off the special banner message'),
        ),
    ]