# Generated by Django 4.0.3 on 2022-05-28 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_delete_bankmodel_cpfmodel_historical_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankModel',
            fields=[
                ('ID', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('DATE', models.DateField()),
                ('YEARMONTH', models.CharField(max_length=10)),
                ('BANK_TYPE', models.CharField(max_length=20)),
                ('VALUE', models.FloatField()),
                ('HISTORICAL', models.BooleanField(default=False)),
            ],
        ),
    ]
