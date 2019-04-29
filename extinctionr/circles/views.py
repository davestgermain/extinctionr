from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views import generic
from .models import Circle, Contact


@login_required
def add_member(request, pk):
	circle = get_object_or_404(Circle, pk=pk)
	email = request.POST['email'].lower()
	name = request.POST['name']
	circle.add_member(email, name)
	return redirect(circle.get_absolute_url())


@login_required
def person_view(request, contact_id):
	contact = get_object_or_404(Contact, pk=contact_id)
	ctx = {'contact': contact}
	return render(request, 'circles/person.html', ctx)


class CircleView(generic.DetailView):
	template_name = 'circles/circle.html'
	def get_queryset(self):
		return Circle.objects.select_related('parent').prefetch_related('leads', 'members')


class TopLevelView(generic.ListView):
	template_name = 'circles/outer.html'

	def get_queryset(self):
		return 	Circle.objects.filter(parent__isnull=True).prefetch_related('leads', 'members')

