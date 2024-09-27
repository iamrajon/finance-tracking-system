from django.urls import path
from a_tracker import views


# list of all urls of a_tracker app

urlpatterns = [
    path('dashboard/', views.index_view, name="home-page"),
    path('transactions/', views.transactions_view, name="transaction-page"),
    path('transactions/create/', views.transactions_create_view, name="create-transaction"),
    path('transactions/detail/<int:id>/', views.transaction_detail_view, name="transaction-detail"),
    path('transaction/<int:pk>/update/', views.transaction_update_view, name="update-transaction"),
    path('transaction/<int:pk>/delete/', views.transaction_delete_view, name="delete-transaction"),
    path('get-transactions/', views.get_transactions_view, name="get-transactions"),
    path('transactions/export', views.export_view, name="export-transaction"),
    path('transactions/import', views.import_view, name="import-transaction"),

    path("transaction/sort", views.transaction_sort_view, name="sort-transaction"),
]
