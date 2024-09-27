from django import forms
from a_tracker.models import Transaction, Category



class TransactionCreationForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.RadioSelect()
    )

    transaction_type = forms.ChoiceField(
        choices=[('', 'Select a transaction type | required')] + list(Transaction.TRANSACTION_TYPE_CHOICES),
        required=True,
    )

    class Meta:
        model = Transaction
        fields = [
            'transaction_type',
            'amount',
            'date',
            'category',
            'details',
            'image',
        ]

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        
        if amount <= 0:
            raise forms.ValidationError("Amount must be a positive number")
        
        return amount
