# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-02 11:17
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20160817_0704'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpreference',
            name='search_preference',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
