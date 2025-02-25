from user import models
from django.db.models import Sum
import resend
from dotenv import load_dotenv
import os
load_dotenv()
resend.api_key = os.getenv('resend')

def send_mail(request,i,x):
    resend.Emails.send({
    "from": "no-reply@test.shubhamasati.tech",
    "to": f"{request.user.email}",
    "subject": "Budget Overflow",
    "html": f"Your Budget is overflowed of category {i} by {x}"
    })
def check(request):
    cat_list=models.Category.objects.filter(user=request.user)
    for i in cat_list:
        budget=models.Budget.objects.filter(category=i,user=request.user)
        budget_amount=0
        total_expense=0
        if budget.first():
            budget_amount=budget.aggregate(total=Sum('amount'))['total'] or 0
            total_expense = (
                models.Transaction.objects
                .filter(category=i, date__gte=budget[0].date,user=request.user)
                .aggregate(total=Sum("amount"))["total"] or 0
            )
        if int(budget_amount) - int(total_expense) < 0:
            x=int(budget_amount) - int(total_expense)
            send_mail(request,i,x)
            return
