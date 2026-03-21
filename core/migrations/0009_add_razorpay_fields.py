from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_dedupe_item_slugs_and_make_unique"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="stripe_charge_id",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="razorpay_payment_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="razorpay_order_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="razorpay_signature",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
