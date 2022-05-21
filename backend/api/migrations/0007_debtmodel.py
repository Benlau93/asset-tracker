# Generated by Django 4.0.3 on 2022-05-21 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_cpfmodel_ref'),
    ]

    operations = [
        migrations.CreateModel(
            name='DebtModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('DATE', models.DateField()),
                ('YEARMONTH', models.CharField(max_length=10)),
                ('DEBT_TYPE', models.CharField(max_length=50)),
                ('DEBT_VALUE', models.FloatField()),
                ('INTEREST_RATE', models.FloatField()),
                ('INTEREST_COMPOUND', models.CharField(max_length=20)),
                ('REPAYMENT', models.FloatField()),
                ('INTEREST', models.FloatField()),
                ('REMAINING_VALUE', models.FloatField()),
            ],
        ),
    ]
