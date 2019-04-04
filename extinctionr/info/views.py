from django.views.generic import TemplateView


class InfoView(TemplateView):
	def get(self, request, *args, **kwargs):
		page = kwargs['page']
		if page.endswith('.html'):
			page = page.split('.')[0]
		self.template_name = page + '.html'
		return super(InfoView, self).get(request, *args, **kwargs)
