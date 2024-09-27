from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from a_tracker.managers import TransactionQuerySet


# Model class for Transaction and Category

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateField(db_index=True)
    image = models.ImageField(upload_to='transactions/images/', null=True, blank=True)
    details = models.TextField(null=True, blank=True)

    objects = TransactionQuerySet.as_manager() # customized manager

    def __str__(self):
        return f"{self.transaction_type} of {self.amount:.2f} on {self.date} by {self.user}"
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'





