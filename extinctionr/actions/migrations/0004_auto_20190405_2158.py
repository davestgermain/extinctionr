# Generated by Django 2.2 on 2019-04-06 01:58

from django.db import migrations
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0003_action_public'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='description',
            field=markdownx.models.MarkdownxField(blank=True, default=''),
        ),
    ]
