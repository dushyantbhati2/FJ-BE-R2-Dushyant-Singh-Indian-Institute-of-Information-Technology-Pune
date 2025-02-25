from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from . import serializers
from . import models
from django.db.models import Sum
from django.db.models.functions import TruncMonth
import json
from datetime import datetime
from utlis import email
from rest_framework.parsers import MultiPartParser
import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from .models import Profile, IncomeSource, Transaction, Budget
from datetime import datetime,timedelta
import os
import tempfile
import matplotlib
matplotlib.use('Agg')  # ✅ Fix: Use non-GUI backend
import matplotlib.pyplot as plt
from fpdf import FPDF
from django.http import HttpResponse
import numpy as np
from django.utils.timezone import now
from django.contrib.auth import logout
class SignUpView(APIView):
    def get(self, request):
        # email.send_mail()
        return render(request, "index.html")

    def post(self, request):
        serializer = serializers.userSerializers(data=request.POST)
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                messages.success(request, "User registered successfully!")
                return redirect("login")
        except ValidationError as e:
            errors = e.detail
            for field, error_list in errors.items():
                for error in error_list:
                    messages.error(request, f"{error}")
        return render(request, "index.html")

class LoginView(APIView):

    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("Home")
        messages.error(request, "Invalid Credentials")
        return render(request, "login.html")

class LogoutView(APIView):
    def get(self, request):
        logout(request)
        messages.success(request, "Logged out successfully!")
        return redirect("login")

class Home(LoginRequiredMixin, APIView):
    login_url = reverse_lazy("login") 
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        categories = models.Category.objects.filter(user=user)
        transactions = models.Transaction.objects.filter(user=user)
        incomes = models.IncomeSource.objects.filter(user=user)
        serial_transactions = serializers.TransactionSerializer(transactions, many=True)
        serial_incomes = serializers.IncomeSerializer(incomes, many=True)
        total_income = models.IncomeSource.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0
        total_expense = models.Transaction.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0
        balance = models.Profile.objects.get(user=user).balance - total_expense + total_income
        receipts=models.Receipts.objects.filter(user=user)
        email.check(request)
        context = {
            "categories": categories,
            "transactions": serial_transactions.data,
            "incomes": serial_incomes.data,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "reciepts":receipts
        }
        return render(request, "home.html", context)

    def post(self, request):
        # Get the selected category from the POST data (using its ID)
        category_id = request.POST.get("category")
        category = get_object_or_404(models.Category, id=category_id, user=request.user)
        
        budget_instance = (
            models.Budget.objects
            .filter(category=category, user=request.user)
            .order_by("date")
            .last()
        )
        if not budget_instance:
            messages.error(request, "No budget found for the selected category.")
            return redirect("Home")
        
        total = models.Budget.objects.filter(category=category, user=request.user).aggregate(total=Sum('amount'))['total'] or 0
                
        total_expense_category = (
            models.Transaction.objects
            .filter(category=category, date__gte=budget_instance.date,user=request.user)
            .aggregate(total=Sum("amount"))["total"] or 0
        )
        
        remaining = total - total_expense_category

        budget_detail = {
            "budget_amount": total,
            "budget_start_date": budget_instance.date,
            "expense_since_budget": total_expense_category,
            "remaining": remaining,
            "category_name": category.name,
        }

        user = request.user
        categories = models.Category.objects.filter(user=user)
        transactions = models.Transaction.objects.filter(user=user)
        incomes = models.IncomeSource.objects.filter(user=user)
        serial_transactions = serializers.TransactionSerializer(transactions, many=True)
        serial_incomes = serializers.IncomeSerializer(incomes, many=True)
        total_income = models.IncomeSource.objects.filter(user=user)\
                        .aggregate(total=Sum("amount"))["total"] or 0
        total_expense_all = models.Transaction.objects.filter(user=user)\
                        .aggregate(total=Sum("amount"))["total"] or 0
        balance = models.Profile.objects.get(user=user).balance - total_expense_all + total_income

        context = {
            "categories": categories,
            "transactions": serial_transactions.data,
            "incomes": serial_incomes.data,
            "total_income": total_income,
            "total_expense": total_expense_all,
            "balance": balance,
            "budget_detail": budget_detail,
        }
        return render(request, "home.html", context)

class IncomeSource(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login") 
    permission_classes = [IsAuthenticated]


    def post(self, request):
        serial = serializers.IncomeSerializer(data=request.data, context={'request': request})
        try:
            if serial.is_valid(raise_exception=True):
                serial.save()
                return redirect("Home")
        except ValidationError as e:
            messages.error(request, e)
        return redirect("Home")

class IncomeDelete(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        source = get_object_or_404(models.IncomeSource, id=pk)
        source.delete()
        return redirect("Home")

class TransactionView(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login") 
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        transactions = models.Transaction.objects.filter(user=user)
        serial = serializers.TransactionSerializer(transactions, many=True)
        return serial.data

    def post(self, request):
        serial = serializers.TransactionSerializer(data=request.data, context={'request': request})
        try:
            if serial.is_valid(raise_exception=True):
                serial.save()
                return redirect("Home")
        except ValidationError as e:
            messages.error(request, e)
        return redirect("Home")

class TransactionDelete(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]
    def post(self,request,pk):
        transcation = get_object_or_404(models.Transaction, id=pk)
        transcation.delete()
        return redirect("Home")

class PieChart(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]
    def get(self,request):
        categories=models.Category.objects.filter(user=request.user)
        data=[]
        category=[]
        for i in categories:
            transactions=models.Transaction.objects.filter(category=i)
            category.append(i.name)
            money=0
            for j in transactions:
                money+=j.amount
            data.append(int(money))
        return Response({"category":category,"amounts":data})

class Bargraph(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]
    def get(self,request):
        transactions=models.Transaction.objects.filter(user=request.user)
        income = models.IncomeSource.objects.filter(user=request.user)
        monthly_expenses = (
            transactions.annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total_amount=Sum("amount"))
            .order_by("month")
        )
        monthly_income = (
            income.annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total_amount=Sum("amount"))
            .order_by("month")
        )
        all_months = {datetime(2024, i, 1).strftime("%b"): {"expenses": 0, "income": 0} for i in range(1, 13)}
        for data in monthly_expenses:
            month = data["month"].strftime("%b")
            all_months[month]["expenses"] = float(data["total_amount"])
        for data in monthly_income:
            month = data["month"].strftime("%b")
            all_months[month]["income"] = float(data["total_amount"])
        labels = list(all_months.keys()) 
        income_data = [all_months[month]["income"] for month in labels]
        expense_data = [all_months[month]["expenses"] for month in labels]
        context = {
            "months": labels,
            "income_data": income_data,
            "expense_data": expense_data,
        }
        print(context)
        return Response(context)

class ReportsView(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]
    def get(self,request):
        report=models.Reports.objects.filter(user=request.user)
        serial=serializers.ReportsSerailizer(report,many=True)
        return serial.data
    def post(self,request):
        user=request.user
        files=request.FILE.get('file')
        name = datetime.now().strftime("%Y%m%d%H%M%S")
        if models.Reports.objects.filter(name=name).exists():
            return redirect("Home")
        models.Reports.objects.create(user=user,file=files)
        return redirect("Home")
    
class BudgetView(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]
    def get(self,request):
        budgets=models.Budget.objects.filter(user=request.user)
        serial=serializers.BugetSerializer(budgets,many=True)
        return serial.data
    def post(self,request):
        serial=serializers.BugetSerializer(data=request.data,context={'request':request})
        try:
            if serial.is_valid(raise_exception=True):
                serial.save()
                return redirect("Home")
        except ValidationError as e:
            messages.error(request, e)
        return redirect("Home")
    
class BudgetDelete(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]
    def post(self,request,pk):
        budget=models.Budget.objects.get(id=pk)
        budget.delete()
        return redirect("Home")

class BudgetByCategory(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]
    def post(self,request):
        category=request.data.get("category")
        cat=models.Category.objects.get(name=category,user=request.user)
        budget=models.Budget.objects.filter(category=cat)
        serial=serializers.BugetSerializer(budget,many=True)
        return serial.data
    
class Receipts(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    def post(self,request):
        serial=serializers.ReceiptSerializer(data=request.data,context={'request': request})
        try:
            if serial.is_valid(raise_exception=True):
                serial.save()
                return redirect("Home")
        except ValidationError as e:
            messages.error(request, e)
        return redirect("Home")
    
class ReceiptsDelete(LoginRequiredMixin,APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]
    def post(self,request,pk):
        receipt=models.Receipts.objects.get(id=pk)
        receipt.delete()
        return redirect("Home")

class SplitExpense(LoginRequiredMixin, APIView):
    login_url = reverse_lazy("login")
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        users=models.User.objects.all()
        # Fetch money you owe
        money_owed = models.ExpenseSplit.objects.filter(participant=user, is_settled=False)
        money_owed_data = {}
        for expense in money_owed:
            payer = expense.shared_expense.payer.username
            money_owed_data[payer] = money_owed_data.get(payer, 0) + float(expense.amount)

        # Fetch money others owe you
        money_lent = models.ExpenseSplit.objects.filter(shared_expense__payer=user, is_settled=False)
        money_lent_data = {}
        for expense in money_lent:
            participant = expense.participant.username
            money_lent_data[participant] = money_lent_data.get(participant, 0) + float(expense.amount)

        # Adjust amounts for mutual debts
        final_money_you_owe = {}
        final_money_others_owe_you = {}

        all_users = set(money_owed_data.keys()) | set(money_lent_data.keys())

        for person in all_users:
            amount_you_owe = money_owed_data.get(person, 0)
            amount_they_owe = money_lent_data.get(person, 0)

            net_amount = amount_you_owe - amount_they_owe  # Calculate the balance

            if net_amount > 0:
                final_money_you_owe[person] = net_amount  # You still owe them
            elif net_amount < 0:
                final_money_others_owe_you[person] = abs(net_amount)  # They owe you

        return render(request, "splitExpense.html", context={
            "money_you_owe": final_money_you_owe,
            "money_others_owe_you": final_money_others_owe_you,
            "users":users
        })



    def post(self, request):
        serial1 = serializers.SharedExpenseSerializer(data=request.data, context={'request': request})
        try:
            if serial1.is_valid(raise_exception=True):
                shared = serial1.save()
                messages.success(request, "Share successfully created.")
        except ValidationError as e:
            messages.error(request, e.detail)
        data = request.data.copy()
        data["shared_expense"] = shared.id
        participant_username = data.getlist("usernames")
        list_username=participant_username[0].split(",")
        data["len"]=len(list_username)
        for i in list_username:
            if i:
                try:
                    participant = models.User.objects.get(username=i)
                    data["participant"] = participant.pk
                except models.User.DoesNotExist:
                    messages.error(request, f"User {i} not found.")
                    return redirect("splitExpense")
            else:
                messages.error(request, "Username is required for participant.")
                return redirect("splitExpense")
            serial = serializers.ExpenseSplitSerializer(data=data, context={'request': request})
            try:
                if serial.is_valid(raise_exception=True):
                    serial.save()
                    messages.success(request, "Expense split successfully created.")
            except ValidationError as e:
                messages.error(request, e.detail)
        return redirect("splitExpense")

class SavingsView(APIView):
    def get(self, request):
        user = request.user
        today = now().date()
        months = [(today - timedelta(days=30 * i)).strftime("%b") for i in range(5, -1, -1)]
        savings_data = []
        user_profile = models.Profile.objects.filter(user=user).first()
        balance = user_profile.balance if user_profile else 0
        for i in range(5, -1, -1):
            start_date = today - timedelta(days=30 * (i + 1))
            end_date = today - timedelta(days=30 * i)

            income = models.IncomeSource.objects.filter(
                user=user, date__range=[start_date, end_date]
            ).aggregate(total_income=Sum("amount"))["total_income"] or 0

            expenses = models.Transaction.objects.filter(
                user=user, date__range=[start_date, end_date]
            ).aggregate(total_expense=Sum("amount"))["total_expense"] or 0

            savings = balance + income - expenses
            savings_data.append(savings)

        return Response({"labels": months, "data": savings_data})

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 14)
        self.cell(200, 10, "Financial Report", ln=True, align='C')
        self.ln(10)

    def add_table(self, header, data, col_widths):
        self.set_font("Arial", 'B', 12)
        for i, col_name in enumerate(header):
            self.cell(col_widths[i], 10, col_name, border=1, align='C')
        self.ln()

        self.set_font("Arial", '', 10)
        for row in data:
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 10, str(cell), border=1, align='C')
            self.ln()
        self.ln(5)

def generate_pdf(request):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    user = request.user
    try:
        profile = models.Profile.objects.get(user=user)
    except models.Profile.DoesNotExist:
        profile = models.Profile.objects.create(user=user)

    incomes = models.IncomeSource.objects.filter(user=user)
    transactions = models.Transaction.objects.filter(user=user)

    # Balance Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, f"Total Balance: INR {profile.balance}", ln=True)
    pdf.ln(5)

    # Income Table
    pdf.cell(200, 10, "Income Sources", ln=True, align='C')
    income_data = [(income.name, f"INR {income.amount}", income.date.strftime('%Y-%m-%d')) for income in incomes]
    pdf.add_table(["Source", "Amount", "Date"], income_data, [80, 50, 50])

    # Transactions Table
    pdf.cell(200, 10, "Transactions", ln=True, align='C')
    transaction_data = [(txn.category.name if txn.category else 'No Category', 
                         f"INR {txn.amount}", txn.date.strftime('%Y-%m-%d')) for txn in transactions]
    pdf.add_table(["Category", "Amount", "Date"], transaction_data, [80, 50, 50])

    # Generate and Embed Graphs
    graph_images = generate_graphs(incomes, transactions, profile.balance)
    
    for graph_img in graph_images:
        pdf.add_page()
        pdf.image(graph_img, x=30, y=50, w=150)
        os.remove(graph_img)  # Delete temp image after adding to PDF

    # ✅ FIXED PDF OUTPUT HANDLING
    response = HttpResponse(pdf.output(dest="S").encode("latin1"), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="financial_report.pdf"'

    return response

def generate_graphs(incomes, transactions, balance):    
    """Generate multiple graphs and return the file paths."""
    graphs = []

    # 1. Bar Chart (Income vs Expenses)
    fig, ax = plt.subplots(figsize=(5, 3))
    income_dates = [inc.date.strftime('%Y-%m-%d') for inc in incomes]
    income_amounts = [inc.amount for inc in incomes]

    expense_dates = [txn.date.strftime('%Y-%m-%d') for txn in transactions]
    expense_amounts = [txn.amount for txn in transactions]

    ax.bar(income_dates, income_amounts, label="Income", color="green")
    ax.bar(expense_dates, expense_amounts, label="Expenses", color="red")

    ax.set_xlabel("Date")
    ax.set_ylabel("Amount (INR)")
    ax.set_title("Income & Expense Overview")
    ax.legend()

    graphs.append(save_plot(fig))

    # 2. Pie Chart (Income Distribution)
    fig, ax = plt.subplots(figsize=(4, 3))
    income_labels = [inc.name for inc in incomes]
    income_values = [inc.amount for inc in incomes]

    ax.pie(income_values, labels=income_labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
    ax.set_title("Income Distribution")

    graphs.append(save_plot(fig))

    # 3. Pie Chart (Expense Distribution)
    fig, ax = plt.subplots(figsize=(4, 3))
    expense_labels = [txn.category.name if txn.category else 'No Category' for txn in transactions]
    expense_values = [txn.amount for txn in transactions]

    ax.pie(expense_values, labels=expense_labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Set3.colors)
    ax.set_title("Expense Distribution")

    graphs.append(save_plot(fig))

    # 4. Line Graph (Savings Over Time)
    fig, ax = plt.subplots(figsize=(5, 3))
    
    total_income = sum(income_amounts) if income_amounts else 0
    total_expense = sum(expense_amounts) if expense_amounts else 0
    savings = total_income - total_expense

    dates = sorted(set(income_dates + expense_dates))
    savings_over_time = [savings for _ in dates]

    ax.plot(dates, savings_over_time, marker='o', linestyle='-', color='blue', label="Savings")
    ax.fill_between(dates, savings_over_time, color='blue', alpha=0.2)

    ax.set_xlabel("Date")
    ax.set_ylabel("Savings (INR)")
    ax.set_title("Savings Over Time")
    ax.legend()

    graphs.append(save_plot(fig))

    return graphs

def save_plot(fig):
    """Saves a matplotlib figure as a temporary file and returns the file path."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(temp_file.name, format="png", dpi=100)
    plt.close(fig)
    
    return temp_file.name  # Return file path for use in PDF
