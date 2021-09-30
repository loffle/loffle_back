# Generated by Django 3.2.6 on 2021-09-30 08:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0002_remove_review_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='questions', to='community.questiontype'),
        ),
        migrations.AlterField(
            model_name='questiontype',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
