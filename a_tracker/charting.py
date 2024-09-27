from collections import defaultdict
import plotly.express as px 
from django.db.models import Sum
from a_tracker.models import Category



def plot_income_expense_bar_chart(qs, width=500, height=350):
    x_vals = ['Income', 'Expenditure']

    # sum up the total income and expenditure
    total_income = qs.filter(transaction_type='income').aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_expense = qs.filter(transaction_type='expense').aggregate(
        total=Sum('amount')
    )['total'] or 0

    fig = px.bar(x=x_vals, y=[total_income, total_expense], width=width, height=height)

    return fig


def plot_category_pie_charts(qs, width=550, height=400):
    count_per_category = (
        qs.order_by('category').values('category')
        .annotate(total=Sum('amount'))
    )

    category_pks = count_per_category.values_list('category', flat=True).order_by('category')
    categories = Category.objects.filter(pk__in=category_pks).order_by('pk').values_list('name', flat=True)
    total_amounts = count_per_category.values_list('total', flat=True)

    if not categories or not total_amounts:  # If no data, return an empty pie chart
        categories = ['No Data']
        total_amounts = [0]

    fig = px.pie(values=total_amounts, names=categories)
    fig.update_layout(width=width, height=height)
    # fig.update_layout(title_text="Total Amount Per Category")
    return fig


# function for line chart
def plot_income_expense_line_chart(qs, width=550, height=350):
    income_data = qs.filter(transaction_type='income').values('date').annotate(
        total=Sum('amount')
    ).order_by('date')

    expense_data = qs.filter(transaction_type='expense').values('date').annotate(
        total=Sum('amount')
    ).order_by('date')

    combined_data = defaultdict(lambda: {'income': 0, 'expense': 0})

    for data in income_data:
        combined_data[data['date']]['income'] = data['total'] or 0

    for data in expense_data:
        combined_data[data['date']]['expense'] = data['total'] or 0

    dates = sorted(combined_data.keys())
    income_totals = [combined_data[date]['income'] for date in dates]
    expense_totals = [combined_data[date]['expense'] for date in dates]

    # If no data, provide at least one point to avoid errors
    if not dates:
        dates = ['No Data']
        income_totals = [0]
        expense_totals = [0]

    fig = px.line(x=dates, y=[income_totals, expense_totals], width=width, height=height)

    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Amount',
        legend_title='Type',
        legend=dict(itemsizing='constant', traceorder='reversed')
    )

    # Add trace names
    if len(fig.data) > 0:
        fig.data[0].name = 'Income'
    if len(fig.data) > 1:
        fig.data[1].name = 'Expense'

    return fig


