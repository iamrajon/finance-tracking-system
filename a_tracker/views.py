from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.conf import settings
from a_tracker.models import Transaction
from a_tracker.filters import TransactionFilter, GraphFilter
from a_tracker.forms import TransactionCreationForm
from a_tracker.charting import (
    plot_income_expense_bar_chart, 
    plot_category_pie_charts,
    plot_income_expense_line_chart
)
from django.contrib import messages
from a_tracker.resources import TransactionResource
from django.http import HttpResponse
from tablib import Dataset


# DashBoard page View
def index_view(request):
    transaction_filter = TransactionFilter(
        request.GET,
        queryset = Transaction.objects.filter(user=request.user)
    )

    try:
        # func call for bar_chart
        income_expense_bar = plot_income_expense_bar_chart(transaction_filter.qs)
        a_bar = income_expense_bar.to_html()

        # function call for pie chart
        category_income_pie = plot_category_pie_charts(transaction_filter.qs.filter(transaction_type='income'))
        category_income_pie.update_layout(title_text="Income PieChart")
        category_income_piechart = category_income_pie.to_html()

        category_expense_pie = plot_category_pie_charts(transaction_filter.qs.filter(transaction_type='expense'))
        category_expense_pie.update_layout(title_text="Expense PieChart")
        category_expense_piechart = category_expense_pie.to_html()

        # function calling for line chart
        income_expense_line = plot_income_expense_line_chart(transaction_filter.qs)
        income_expense_linechart = income_expense_line.to_html()

    except ValueError as e:
        # Handle error (e.g., no data)
        a_bar = "<p>No data available to generate bar chart.</p>"
        category_income_piechart = "<p>No income data available to generate pie chart.</p>"
        category_expense_piechart = "<p>No expense data available to generate pie chart.</p>"
        income_expense_linechart = "<p>No data available to generate line chart.</p>"


    total_income = transaction_filter.qs.get_total_income() or 0
    total_expense = transaction_filter.qs.get_total_expenses() or 0
    net_income = total_income - total_expense

    context = {
        'filter': transaction_filter,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_income': net_income,
        'income_expense_barchart1': a_bar,
        'category_income_piechart': category_income_piechart,
        'category_expense_piechart': category_expense_piechart,
        'income_expense_linechart': income_expense_linechart
    }

    if request.htmx:
        return render(request, 'partials/graph-container.html', context)
    return render(request, 'tracker/index.html', context)



@login_required()
def transactions_view(request):
    # transactions = Transaction.objects.filter(user=request.user)

    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )

    paginator = Paginator(transaction_filter.qs, settings.PAGE_SIZE)
    transaction_page = paginator.page(1)

    total_income = transaction_filter.qs.get_total_income()
    total_expense = transaction_filter.qs.get_total_expenses()
    net_income = total_income - total_expense

    context = {
        'transactions': transaction_page,
        'filter': transaction_filter,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_income': net_income
        }
    if request.htmx:
        return render(request, "partials/transaction-container.html", context)
    return render(request, 'tracker/transactions.html', context)

# view for infinite scroll and pagination
@login_required
def get_transactions_view(request):
    import time
    time.sleep(1)
    page = request.GET.get('page', 1)
    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )

    paginator = Paginator(transaction_filter.qs, settings.PAGE_SIZE)

    context = {
        'transactions': paginator.page(page)
    }
    return render(request, "partials/transaction-container.html#transaction_page", context)



# view function for creating transaction
@login_required
def transactions_create_view(request):
    if request.method == "POST":
        form = TransactionCreationForm(request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('transaction-page')
        else:
            context = {'form': form}
            return render(request, 'tracker/create-transaction.html', context)
    else:
        form = TransactionCreationForm()

    context = {'form': form}
    return render(request, 'tracker/create-transaction.html', context)


# transaction detail view
@login_required
def transaction_detail_view(request, id):
    if id:
        # print(f"Id is: {id}")
        transaction = get_object_or_404(Transaction, id=id, user=request.user)
        print(f"Transaction: {transaction} Type: {type(transaction)}")
    
    context = {'transaction': transaction}
    return render(request, "tracker/transaction-detail.html", context)

# transaction update view
@login_required
def transaction_update_view(request, pk):

    transaction = get_object_or_404(Transaction, id=pk)

    if request.method == "POST":
        form = TransactionCreationForm(request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction is updated successfully!")
            return redirect('transaction-page')
        else:
            context = {'form': form, 'transaction': transaction}
            return render(request, "tracker/update-transaction.html", context)

    form = TransactionCreationForm(instance=transaction)
    context = {'form': form, 'transaction': transaction}
    return render(request, "tracker/update-transaction.html", context)


# view function for deleting the transaction
@login_required
@require_http_methods(['DELETE', 'GET'])
def transaction_delete_view(request, pk):
    
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if transaction:
        transaction.delete()
        messages.success(request, "Transaction Deleted Successfully")
        return redirect('transaction-page')
    else:
        context = {'transaction': transaction}
        messages.error(request, "Transaction, you want to delete Not Found")
        return render(request, "tracker/transaction-detail.html", context)


@login_required
def export_view(request):
    if request.htmx:
        return HttpResponse(headers={'HX-Redirect': request.get_full_path()})
    
    transaction_filter = TransactionFilter(
        request.GET,
        queryset = Transaction.objects.filter(user=request.user).select_related('category')
    )

    data = TransactionResource().export(transaction_filter.qs)
    response = HttpResponse(data.csv)
    response['Content-Disposition'] = 'attachment; filename="transaction.csv"'
    return response


# view for bulk importing transaction
@login_required
def import_view(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        resource = TransactionResource()
        dataset = Dataset()
        dataset.load(file.read().decode(), format="csv")
        result = resource.import_data(dataset, user=request.user, dry_run=True)

        for row in result:
            for error in row.errors:
                print("Error", error)

        if not result.has_errors():
            resource.import_data(dataset, user=request.user, dry_run=False)
            messages.success(request, f"{len(dataset)} data has been imported from given csv file to database")
            return redirect("transaction-page")
        else:
            messages.error(request, "Unable to import data from given csv file!")
            return redirect("import-transaction")
    return render(request, "partials/import-transaction.html")


# quick sort
def quick_sort(arr, key_func, reverse=False):
    """ Sorts the list 'arr' using quicksort algorithm with the given key function. """
    if len(arr) <= 1:
        return arr
    else:
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if (key_func(x) < key_func(pivot)) ^ reverse]
        middle = [x for x in arr if key_func(x) == key_func(pivot)]
        right = [x for x in arr if (key_func(x) > key_func(pivot)) ^ reverse]
        return quick_sort(left, key_func, reverse) + middle + quick_sort(right, key_func, reverse)


# sort transaction view
@login_required
def transaction_sort_view(request):
    sort_by = request.GET.get('sort_by', 'latest')

    transaction_filter = TransactionFilter(
        request.GET,
        queryset = Transaction.objects.filter(user=request.user).select_related('category')
    )

    # changing to list for performing quick sort
    transactions_list = list(transaction_filter.qs)

    if sort_by == 'high_amount':
        # sorted_transactions = quick_sort(transactions_list, key_func=lambda x: x.amount, reverse=True)
        sorted_transactions = transaction_filter.qs.order_by("-amount")
    elif sort_by == 'low_amount':
        # sorted_transactions = quick_sort(transactions_list, key_func=lambda x: x.amount, reverse=False)
        sorted_transactions = transaction_filter.qs.order_by("amount")
    elif sort_by == 'oldest':
        # sorted_transactions = quick_sort(transactions_list, key_func=lambda x: x.date, reverse=False)
        sorted_transactions = transaction_filter.qs.order_by("date")
    else:  # Default to 'last_modified'
        # sorted_transactions = quick_sort(transactions_list, key_func=lambda x: x.date, reverse=True)
        sorted_transactions = transaction_filter.qs.order_by("-date")

    total_income = transaction_filter.qs.get_total_income()
    total_expense = transaction_filter.qs.get_total_expenses()
    net_income = total_income - total_expense

    context = {
        'transactions': sorted_transactions,
        'filter': transaction_filter,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_income': net_income
        }

    if request.htmx:
        return render(request, "partials/transaction-container.html", context)




