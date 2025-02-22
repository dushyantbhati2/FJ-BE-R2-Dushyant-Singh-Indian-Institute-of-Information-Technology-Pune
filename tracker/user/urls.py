from django.urls import path
from . import views
urlpatterns = [
    path('register',views.SignUpView.as_view(),name="register"),
    path('',views.Home.as_view(),name="Home"),
    path('login',views.LoginView.as_view(),name="login"),
    path('transaction',views.TransactionView.as_view(),name="transaction"),
    path('income',views.IncomeSource.as_view(),name="income"),
    # path('',)
]
