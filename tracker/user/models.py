from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4
# Create your models here.
class Profile(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    balance=models.IntegerField(default=0)  
    def __str__(self):
        return self.user.username

class IncomeSource(models.Model):
    id=models.UUIDField(default=uuid4,primary_key=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=255)
    amount=models.IntegerField()
    date=models.DateField()
 
    def __str__(self):
        return self.name

class Category(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=255)
    def __str__(self):
        return self.name
    
class Transaction(models.Model):
    id=models.UUIDField(default=uuid4,primary_key=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    category = models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.amount} on {self.date}"
    

class Budget(models.Model):
    id=models.UUIDField(default=uuid4,primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    def __str__(self):
        return f"Budget for {self.category.name}: {self.amount}"
    
class Reports(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    file=models.FileField(upload_to="documents")
    name=models.CharField(max_length=255)
    def __str__(self):
        return f"{self.name} + {self.user.username}"
    
class Receipts(models.Model):
    id=models.UUIDField(default=uuid4,primary_key=True)
    file=models.FileField(upload_to="documents")
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    def __str__(self):
        return self.user.username
    
class SharedExpense(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shared_expenses")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    def __str__(self):
        return f"Shared Expense ({self.date}): {self.description} - {self.amount}"

class ExpenseSplit(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    shared_expense = models.ForeignKey(SharedExpense, on_delete=models.CASCADE, related_name="splits")
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expense_splits")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_settled = models.BooleanField(default=False,blank=True)
    def __str__(self):
        return f"{self.participant.username} owes {self.amount} for {self.shared_expense}"