from django.contrib import admin

from .models import Agent, SanctionedEntity, ScreeningCase, Match

admin.site.register(Agent)
admin.site.register(SanctionedEntity)
admin.site.register(ScreeningCase)
admin.site.register(Match)