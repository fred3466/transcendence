# Generated by Django 5.1.3 on 2024-11-28 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0073_alter_profile_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='description',
            field=models.CharField(default='Darius: The Hand of Noxus, a brutal warrior with a deadly axe.'),
        ),
    ]
