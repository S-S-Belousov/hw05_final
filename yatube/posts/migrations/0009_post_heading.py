# Generated by Django 2.2.16 on 2023-03-01 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_follow'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='heading',
            field=models.CharField(default='Нет заголовка', max_length=200),
            preserve_default=False,
        ),
    ]
