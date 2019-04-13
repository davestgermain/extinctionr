from django.db import models
from django.urls import reverse
from markdownx.models import MarkdownxField
from django.utils.timezone import now
from django.contrib.auth import get_user_model


class PressReleaseManager(models.Manager):
    def released(self):
        return self.get_queryset().filter(released__lt=now()).order_by('released')


class PressRelease(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True)
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    released = models.DateTimeField(db_index=True, null=True, blank=True, help_text='Release dates in the future will not be visible on the site')
    body = MarkdownxField(default='', blank=True)

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