# Generated by Django 3.0.6 on 2020-07-02 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='banner',
            field=models.ImageField(default='http://fancys3bucket.amazonaws.com/media/banner_pics/facade.jpg', upload_to='banner_pics'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='picture',
            field=models.ImageField(default='http://fancys3bucket.amazonaws.com/media/profile_pics/roboraptor.jpg', upload_to='profile_pics'),
        ),
    ]