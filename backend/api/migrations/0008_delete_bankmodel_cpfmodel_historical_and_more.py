# Generated by Django 4.0.3 on 2022-05-28 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_debtmodel'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BankModel',
        ),
        migrations.AddField(
            model_name='cpfmodel',
            name='HISTORICAL',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='cpfmodel',
            name='ID',
            field=models.CharField(max_length=50, primary_key=True, serialize=False),
        ),
    ]
