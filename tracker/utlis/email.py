from user import models
from django.db.models import Sum
import resend

resend.api_key = "re_5hGa6etJ_PvHBh3GAcur3niJoCMGTb37X"

def send_mail():
    resend.Emails.send({
    "from": "onboarding@resend.dev",
    "to": "112215063@cse.iiitp.ac.in",
    "subject": "Hello World",
    "html": "<p>Congrats on sending your <strong>first email</strong>!</p>"
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
                .filter(category=i, date__gte=budget.date,user=request.user)
                .aggregate(total=Sum("amount"))["total"] or 0
            )
        if int(budget_amount) - int(total_expense) < 0:
            send_mail()
            return
