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


    login_url = reverse_lazy("login") 
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        categories=models.Category.objects.filter(user=user)
        transactions = models.Transaction.objects.filter(user=user)
        incomes = models.IncomeSource.objects.filter(user=user)
        serial_transactions = serializers.TransactionSerializer(transactions, many=True)
        serial_incomes = serializers.IncomeSerializer(incomes, many=True)
        total_income = models.IncomeSource.objects.filter(user=user).aggregate(total=Sum('amount'))['total']
        if total_income is None:
            total_income=0
        total_expense=models.Transaction.objects.filter(user=user).aggregate(total=Sum('amount'))['total']
        if total_expense is None:
            total_expense=0
        balance=models.Profile.objects.get(user=user).balance
        balance=balance-total_expense+total_income
        # email.check(request)
        return render(request, "home.html", {"categories":categories,"transactions": serial_transactions.data, "incomes": serial_incomes.data,"total_expense":total_expense,"total_income":total_income,"balance":balance})
    from django.shortcuts import render, get_object_or_404, redirect

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

    def get(self, request):
        user = request.user
        sources = models.IncomeSource.objects.filter(user=user)
        serial = serializers.IncomeSerializer(sources, many=True)
        return serial.data

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