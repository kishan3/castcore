# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-08 12:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0003_auto_20160812_0922'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='hair_color',
            field=models.CharField(blank=True, choices=[('black', 'black'), ('dark_brown', 'dark_brown'), ('light_brown', 'light_brown'), ('blonde', 'blonde'), ('red', 'red'), ('grey', 'grey'), ('white', 'white'), ('', 'does_not_matter')], default='', help_text='Peferred eye color.', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='hair_style',
            field=models.CharField(blank=True, choices=[('partially_bald', 'partially_bald'), ('completely_bald', 'completely_bald'), ('shoulder_length', 'shoulder_length'), ('army_cut', 'army_cut'), ('normal', 'normal'), ('slightly_long', 'slightly_long'), ('boy_cut', 'boy_cut'), ('bust_length', 'bust_length'), ('waist_length', 'waist_length'), ('knee_length', 'knee_length')], default='', help_text='Peferred eye color.', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='job_owner_email',
            field=models.EmailField(blank=True, help_text='Should be valid email, e.g. name@example.com', max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='job_owner_phone',
            field=models.CharField(blank=True, db_index=True, help_text="User's phone number.", max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='body_type',
            field=models.CharField(blank=True, choices=[('skinny', 'skinny'), ('slim', 'slim'), ('athletic', 'athletic'), ('muscular', 'muscular'), ('heavy', 'heavy'), ('bulky', 'bulky'), ('very_fat', 'very_fat'), ('curvy', 'curvy'), ('very_heavy', 'very_heavy'), ('', 'does_not_matter')], default='', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='eye_color',
            field=models.CharField(blank=True, choices=[('black', 'black'), ('blue', 'blue'), ('dark_brown', 'dark_brown'), ('light_brown', 'light_brown'), ('green', 'green'), ('grey', 'grey'), ('violet', 'violet'), ('hazel', 'hazel'), ('', 'does_not_matter')], default='', help_text='Peferred eye color.', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='skin_type',
            field=models.CharField(blank=True, choices=[('very_fair', 'very_fair'), ('fair', 'fair'), ('wheatish', 'wheatish'), ('dusky', 'dusky'), ('dark', 'dark'), ('very_dark', 'very_dark'), ('', 'does_not_matter')], default='', help_text='Preferred skin type.', max_length=50, null=True),
        ),
    ]
