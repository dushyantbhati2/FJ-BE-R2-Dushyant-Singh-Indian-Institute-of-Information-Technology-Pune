from django.contrib import admin
from . import models
# Register your models here.

admin.site.register(models.Budget)
admin.site.register(models.Category)
admin.site.register(models.IncomeSource)
admin.site.register(models.Transaction)
admin.site.register(models.Reports)
admin.site.register(models.Profile)
admin.site.register(models.Receipts)
admin.site.register(models.SharedExpense)
admin.site.register(models.ExpenseSplit)
# admin.site.register(models.Budget)