from django.db import models
from django.urls import reverse
from markdownx.models import MarkdownxField


class PressRelease(models.Model):
	title = models.CharField(max_length=255, db_index=True)
	slug = models.SlugField(unique=True)
	created = models.DateTimeField(db_index=True)
	released = models.DateTimeField(db_index=True, null=True, blank=True)
	body = MarkdownxField(default='', blank=True)

	def get_absolute_url(self):
		return reverse('extinctionr.info:pr-detail', kwargs={'slug': self.slug})
