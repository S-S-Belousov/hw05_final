# Generated by Django 2.2.16 on 2023-03-01 17:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_post_heading'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='heading',
        ),
    ]