# Generated by Django 4.2.1 on 2023-06-06 22:00

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_alter_chorestatus_name_delete_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chorestatus',
            name='color',
            field=colorfield.fields.ColorField(blank=True, default=None, image_field=None, max_length=200, null=True, samples=None, unique=True),
        ),
    ]
