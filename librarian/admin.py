from .models import Person, Paper, Institution,Journal,Country,Citation
from django.contrib import admin


admin.site.register(Person)
admin.site.register(Paper)
admin.site.register(Institution)
admin.site.register(Journal)
admin.site.register(Country)
admin.site.register(Citation)
