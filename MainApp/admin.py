from django.contrib import admin
from .models import Resume, ResumeComment, Vacancy, VacancyApplication


admin.site.register(Resume)
admin.site.register(ResumeComment)
admin.site.register(Vacancy)
admin.site.register(VacancyApplication)