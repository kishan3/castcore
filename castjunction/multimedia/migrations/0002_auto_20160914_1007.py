# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-14 10:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multimedia', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audio',
            name='audio_type',
            field=models.CharField(choices=[('P', 'Primary'), ('G', 'Generic'), ('C', 'Cover')], default='G', max_length=1),
        ),
        migrations.AlterField(
            model_name='image',
            name='image_type',
            field=models.CharField(choices=[('P', 'Primary'), ('G', 'Generic'), ('C', 'Cover')], default='G', max_length=1),
        ),
        migrations.AlterField(
            model_name='video',
            name='video_type',
            field=models.CharField(choices=[('P', 'Primary'), ('G', 'Generic'), ('C', 'Cover')], default='G', max_length=1),
        ),
    ]
