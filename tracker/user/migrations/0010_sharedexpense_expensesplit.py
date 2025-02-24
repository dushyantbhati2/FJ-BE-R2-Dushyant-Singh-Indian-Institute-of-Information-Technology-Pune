# Generated by Django 5.1.6 on 2025-02-24 06:13

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_alter_profile_balance_receipts'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedExpense',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField(blank=True, null=True)),
                ('date', models.DateField()),
                ('payer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shared_expenses', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseSplit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('amount_owed', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_settled', models.BooleanField(default=False)),
                ('participant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expense_splits', to=settings.AUTH_USER_MODEL)),
                ('shared_expense', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='splits', to='user.sharedexpense')),
            ],
        ),
    ]
