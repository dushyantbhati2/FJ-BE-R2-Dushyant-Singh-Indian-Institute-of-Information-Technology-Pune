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
class SignUpView(APIView):
    def get(self, request):
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

class Home(LoginRequiredMixin,APIView):
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
        return render(request, "home.html", {"categories":categories,"transactions": serial_transactions.data, "incomes": serial_incomes.data,"total_expense":total_expense,"total_income":total_income,"balance":balance})

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