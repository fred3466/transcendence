# Generated by Django 5.1.3 on 2024-11-19 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0035_alter_profile_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='description',
            field=models.CharField(default='Garen: The Might of Demacia, a noble warrior with a powerful spinning strike.'),
        ),
    ]