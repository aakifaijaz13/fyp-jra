# Generated by Django 4.2.1 on 2023-06-13 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campusrecruiter', '0016_verifier'),
    ]

    operations = [
        migrations.AddField(
            model_name='verifier',
            name='type',
            field=models.CharField(default=' ', max_length=50),
            preserve_default=False,
        ),
    ]
