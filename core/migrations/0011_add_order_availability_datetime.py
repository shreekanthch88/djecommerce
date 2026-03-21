from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_add_address_lat_lng"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="availability_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="availability_time",
            field=models.TimeField(blank=True, null=True),
        ),
    ]
