from django.shortcuts import render,redirect,get_list_or_404,get_object_or_404
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from . import serializers
from . import models
from django.contrib.auth import authenticate
import json
# Create your views here.
class SignUpView(APIView):
    def get(self,request):
        return render(request,"index.html")
    def post(self,request):
        serializer=serializers.userSerializers(data=request.POST)
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                messages.success(request, "User registered successfully!")
                return redirect("Home")
        except ValidationError as e:
            # print(e)
            errors = e.detail
            for field, error_list in errors.items():
                for error in error_list:
                    messages.error(request, f"{error}")
        return render(request,"index.html")

class LoginView(APIView):
    def get(self,request):
        return render(request,"login.html")
    def post(self,request):
        username=request.POST.get("username")
        password=request.POST.get("password")
        user=authenticate(username=username,password=password)
        if user is not None:
            return redirect("Home")
        messages.error(request,"Invalid Credentials")
        return render(request,"login.html")

class Home(APIView):
    def get(self,request):
        user=request.user
        transcation=get_list_or_404(models.Transaction,user=user)
        income=get_list_or_404(models.IncomeSource,user=user)
        serialtranscation=serializers.TransactionSerializer(transcation,many=True)
        serialincome=serializers.IncomeSerializer(income,many=True)
        return render(request,"home.html",{'transactions':serialtranscation.data,'incomes':serialincome.data})
    
class IncomeSource(APIView):
    def get(self,request):
        user=request.user
        sources=get_list_or_404(models.IncomeSource,user=user)
        serial=serializers.IncomeSerializer(sources)
        return serial
    
    def post(self,request):
        serial=serializers.IncomeSerializer(data=request.data,context={'request':request})
        try:
            if serial.is_valid(raise_exception=True):
                serial.save()
                return redirect("Home")
        except Exception as e:
            messages.error(request,e)
        return redirect("Home")
    
    def delete(self,request,pk):
        get_object_or_404(IncomeSource,id=pk).delete()
        return redirect("Home")
    
class TransactionView(APIView):
    def get(self,request):
        user=request.user
        sources=get_list_or_404(models.Transaction,user=user)
        serial=serializers.TransactionSerializer(sources)
        return serial
    
    def post(self,request):
        serial=serializers.TransactionSerializer(data=request.data,context={'request': request})
        try:
            if serial.is_valid(raise_exception=True):
                serial.save()
                return redirect("Home")
        except Exception as e:
            messages.error(request,e)
        return redirect("Home")
    
    def delete(self,request,pk):
        get_object_or_404(models.Transaction,id=pk).delete()
        return redirect("Home")


