from django.views.generic import TemplateView
from django.http import Http404
from django.template.loader import get_template, TemplateDoesNotExist


class InfoView(TemplateView):
	def get(self, request, *args, **kwargs):
		page = kwargs['page']
		if page.endswith('.html'):
			page = page.split('.')[0]
		try:
			template_name = 'pages/%s.html' % page
			get_template(template_name)
			self.template_name = template_name
			return super(InfoView, self).get(request, *args, **kwargs)
		except TemplateDoesNotExist:
			raise Http404(page)

