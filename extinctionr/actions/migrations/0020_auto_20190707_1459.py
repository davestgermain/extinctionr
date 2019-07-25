# Generated by Django 2.2.1 on 2019-07-07 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0019_action_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='location',
            field=models.TextField(blank=True, default='', help_text='Event location will be converted to a google maps link, unless you format it as a Markdown link -- [something](http://foo.com)'),
        ),
    ]