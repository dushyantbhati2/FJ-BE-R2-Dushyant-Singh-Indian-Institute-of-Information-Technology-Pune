from django.urls import path
from . import views
urlpatterns = [
    path('register',views.SignUpView.as_view(),name="register"),
    path('',views.Home.as_view(),name="Home"),
    path('login',views.LoginView.as_view(),name="login"),
    path('transaction',views.TransactionView.as_view(),name="transaction"),
    path('transaction/<uuid:pk>',views.TransactionDelete.as_view(),name="transactionDelete"),
    path('income',views.IncomeSource.as_view(),name="income"),
    path('incomedelete/<uuid:pk>',views.IncomeDelete.as_view(),name="incomedelete"),
    path('piechart',views.PieChart.as_view(),name="piechart"),
    path('bargraph',views.Bargraph.as_view(),name="bargraph"),
    path('budget',views.BudgetView.as_view(),name="budget"),
    path('budget/<uuid:pk>',views.BudgetDelete.as_view(),name="budgetdelete"),
    path('receipt',views.Receipts.as_view(),name="receipt"),
    path('receipt/<uuid:pk>',views.ReceiptsDelete.as_view(),name="receiptdelete"),
    path('split_expense',views.SplitExpense.as_view(),name="splitExpense"),
    path('generate_report/', views.generate_pdf, name='generate_financial_report'),
    # path('',)
]
