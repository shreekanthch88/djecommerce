from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_add_order_availability_datetime"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="phone_number",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="profile_picture",
            field=models.ImageField(blank=True, null=True, upload_to="profiles/"),
        ),
    ]
