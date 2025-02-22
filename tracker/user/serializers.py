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
        print(data)
        if data.get("password")!=self.initial_data.get("cnfpassword"):
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
        fields = ['user', 'description', 'amount', 'date', 'category']

    def create(self, validated_data):
        category_name = validated_data.pop("category")
        cat = models.Category.objects.create(
            name=category_name,
            user=self.context["request"].user
        )
        validated_data["category"] = cat
        return models.Transaction.objects.create(**validated_data)

    