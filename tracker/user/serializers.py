from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer,ValidationError
from rest_framework.response import Response
from rest_framework import status
from . import models

class userSerializers(ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if self.initial_data.get("balance") is None:
            raise ValidationError({'error':'balance field is nescessary'})
        elif data.get("password")!=self.initial_data.get("cnfpassword"):
            raise ValidationError({'error':'Password dont match'})
        if User.objects.filter(username=data.get("username")).exists():
            raise ValidationError({'error':'Username already taken'})
        elif User.objects.filter(email=data.get("email")).exists():
            raise ValidationError({'error':'email already taken'})
        return data
    
    def create(self, validated_data):
        user = User(username=validated_data["username"],email=validated_data["email"])
        user.set_password(validated_data["password"])
        user.save()
        models.Profile.objects.create(user=user,balance=self.initial_data.get("balance"))
        return user
    
class IncomeSerializer(ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model=models.IncomeSource
        fields='__all__'

    def create(self, validated_data):
        return models.IncomeSource.objects.create(**validated_data)
    
class TransactionSerializer(ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    category = serializers.CharField()

    class Meta:
        model = models.Transaction
        fields = ['id','user', 'description', 'amount', 'date', 'category']

    def create(self, validated_data):
        category_name = validated_data.pop("category")
        user = self.context["request"].user
        category = models.Category.objects.filter(name=category_name, user=user).first()
        if not category:
            category = models.Category.objects.create(name=category_name, user=user)
        validated_data["category"] = category
        return models.Transaction.objects.create(**validated_data)

class ProfileSerializer(ModelSerializer):
    class Meta:
        model=models.Profile
        fields='__all__'

class BugetSerializer(ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    category = serializers.CharField()
    class Meta:
        model=models.Budget
        fields='__all__'
    def create(self, validated_data):
        category_name = validated_data.pop("category")
        user = self.context["request"].user
        category = models.Category.objects.filter(name=category_name, user=user).first()
        if not category:
            category = models.Category.objects.create(name=category_name, user=user)
        validated_data["category"] = category
        return models.Budget.objects.create(**validated_data)
        
class ReportsSerailizer(ModelSerializer):
    class Meta:
        model=models.Reports
        fields='__all__'
    

class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Receipts
        fields = ['file']
    def create(self, validated_data):
        user = self.context['request'].user
        return models.Receipts.objects.create(user=user, **validated_data)
    
class SharedExpenseSerializer(serializers.ModelSerializer):
    payer=serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = models.SharedExpense
        fields = '__all__'


class ExpenseSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ExpenseSplit
        fields = '__all__'
    def create(self, validated_data):
        validated_data["amount"]=int(validated_data["amount"])/(self.initial_data.get("len")+1)
        return models.ExpenseSplit.objects.create(**validated_data)


        

