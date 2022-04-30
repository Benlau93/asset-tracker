# Generated by Django 4.0.3 on 2022-04-29 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_remove_cpfmodel_account_type_remove_cpfmodel_value_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cpfmodel',
            name='id',
        ),
        migrations.AddField(
            model_name='bankmodel',
            name='YEARMONTH',
            field=models.CharField(default=0, max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cpfmodel',
            name='ID',
            field=models.IntegerField(default=0, primary_key=True, serialize=False),
            preserve_default=False,
        ),
    ]