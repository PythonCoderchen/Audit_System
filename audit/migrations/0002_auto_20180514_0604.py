# Generated by Django 2.0.5 on 2018-05-14 06:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='auditlog',
            name='cmd',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='date',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='session',
        ),
    ]
