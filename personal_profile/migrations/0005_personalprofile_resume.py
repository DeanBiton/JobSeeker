# Generated by Django 4.0.3 on 2022-03-20 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal_profile', '0004_alter_personalprofile_birth_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='personalprofile',
            name='resume',
            field=models.FileField(null=True, upload_to='resumes'),
        ),
    ]