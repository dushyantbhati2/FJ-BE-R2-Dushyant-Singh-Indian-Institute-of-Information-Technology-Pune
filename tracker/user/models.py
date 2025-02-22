from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4
# Create your models here.
class IncomeSource(models.Model):
    id=models.UUIDField(default=uuid4,primary_key=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=255)
    amount=models.IntegerField()
    date=models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=255)
    def __str__(self):
        return self.name
    
class Transaction(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    category = models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.category.name} - {self.amount} on {self.date}"
    

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f"Budget for {self.category.name}: {self.amount}"