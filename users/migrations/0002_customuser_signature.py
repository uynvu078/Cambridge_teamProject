# Generated by Django 5.1.7 on 2025-03-17 23:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="signature",
            field=models.ImageField(blank=True, null=True, upload_to="signatures/"),
        ),
    ]
