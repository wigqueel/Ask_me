# Generated by Django 3.0.4 on 2020-06-22 07:49

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0010_auto_20200622_0748'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]