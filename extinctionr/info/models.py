from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from markdownx.models import MarkdownxField


class PressReleaseManager(models.Manager):
    def released(self):
        return self.get_queryset().filter(released__lt=now()).order_by('-released')


class PressRelease(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True)
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    released = models.DateTimeField(db_index=True, null=True, blank=True, help_text='Release dates in the future will not be visible on the site')
    body = MarkdownxField(default='', blank=True)
    modified = models.DateTimeField(auto_now=True)

    objects = PressReleaseManager()

    @property
    def is_released(self):
        return self.released and self.released <= now()

    def get_absolute_url(self):
        return reverse('extinctionr.info:pr-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


class Photo(models.Model):
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    uploader = models.ForeignKey(get_user_model(), null=True, on_delete=models.SET_NULL)
    photo = models.ImageField(upload_to='photos', width_field='width', height_field='height')
    caption = models.TextField(default='', blank=True)
    width = models.IntegerField(default=0, blank=True)
    height = models.IntegerField(default=0, blank=True)
    public = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return '{} by {}'.format(self.photo, self.uploader)

    def thumbnail_tag(self):
        return mark_safe('<img class="img img-fluid" width=256 src="%s" />' % self.photo.url)
    thumbnail_tag.short_description = 'Image'

# Model for all the XR chapters in MA
class Chapter(models.Model):
    title = models.CharField(max_length=64, db_index=True)
    description = models.TextField(default='', blank=True)
    lat = models.FloatField(default=0.0, blank=True)
    lng = models.FloatField(default=0.0, blank=True)
    site = models.CharField(max_length=255)
    join = models.CharField(max_length=255)
    facebook = models.CharField(max_length=255)
    twitter = models.CharField(max_length=255)

    def __str__(self):
        return self.title

