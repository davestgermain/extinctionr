# Generated by Django 3.0.6 on 2020-05-25 21:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('news', '0006_auto_20200515_1835'),
    ]

    operations = [
        migrations.AddField(
            model_name='storypage',
            name='anonymous',
            field=models.BooleanField(default=False, help_text='When checked, story author will be XR Boston'),
        ),
        migrations.AddField(
            model_name='storypage',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='storypage',
            name='categories',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, help_text='The set of categories this page will be served', to='news.StoryCategory'),
        ),
        migrations.AlterField(
            model_name='storypage',
            name='lede',
            field=models.CharField(help_text='A short intro that appears in the story index page', max_length=1024),
        ),
    ]