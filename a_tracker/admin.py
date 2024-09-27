from django.contrib import admin
from a_tracker.models import Transaction, Category


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'transaction_type', 'category', 'amount', 'date']
    search_fields = ['category__name']



admin.site.register(Category, CategoryAdmin)