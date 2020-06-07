# Generated by Django 3.0.6 on 2020-06-02 21:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0045_assign_unlock_grouppagepermission'),
        ('news', '0009_auto_20200531_1702'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpecialNotice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(help_text='Message will appear at the top of every page', max_length=255)),
                ('link', models.URLField(help_text='The url to the page the message should link to')),
                ('color', models.CharField(help_text='Pick a color for the banner', max_length=8)),
                ('enabled', models.BooleanField(help_text='Turn off the special banner message')),
                ('site', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.Site')),
            ],
            options={
                'verbose_name': 'Special banner message',
            },
        ),
    ]