# Generated by Django 4.2.1 on 2023-06-14 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campusrecruiter', '0018_delete_verifier'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='Approved',
            field=models.CharField(default=False, max_length=50),
        ),
    ]
