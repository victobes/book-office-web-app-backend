# Generated by Django 5.1.1 on 2024-11-12 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book_production', '0003_alter_bookproductionservice_image_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selectedservices',
            name='rate',
            field=models.CharField(choices=[('BASE', 'Base'), ('PREMIUM', 'Premium'), ('PROFESSIONAL', 'Professional')], default='BASE', max_length=20),
        ),
    ]