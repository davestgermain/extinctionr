import datetime
from django.db import models
from django.contrib.auth import get_user_model
from contacts.models import Contact


USER_MODEL = get_user_model()


class Action(models.Model):
	name = models.CharField(max_length=255, db_index=True)
	when = models.DateTimeField(db_index=True)
	description = models.TextField(default='', blank=True)

	def signup(self, email, role, notes='', promised=None):
		db_role = ActionRole.objects.get_or_create(name=role)[0]
		try:
			user = Contact.objects.get(email=email)
		except Contact.DoesNotExist:
			first_name = last_name = ''
			user = Contact.objects.create(email=email, first_name=first_name, last_name=last_name)
		if promised:
			promised = datetime.datetime.now()
		atten, created = Attendee.objects.get_or_create(action=self, contact=user, role=db_role, notes=notes, promised=promised)
		if not created:
			if notes:
				atten.notes = notes
			if promised:
				atten.promised = promised
			atten.save()
		return atten

	def __str__(self):
		return '%s on %s' % (self.name, self.when.strftime('%b %e, %Y @ %H:%M'))


class ActionRole(models.Model):
	name = models.CharField(max_length=100, db_index=True, unique=True)

	def __str__(self):
		return self.name


class Attendee(models.Model):
	action = models.ForeignKey(Action, on_delete=models.CASCADE)
	contact = models.ForeignKey(Contact, on_delete=models.DO_NOTHING)
	role = models.ForeignKey(ActionRole, on_delete=models.DO_NOTHING)
	promised = models.DateTimeField(null=True, blank=True)
	notes = models.TextField(default='', blank=True)

	class Meta:
		unique_together = ('action', 'contact', 'role')

	def __repr__(self):
		return '%s %s %s' % (self.action, self.contact, self.role)
