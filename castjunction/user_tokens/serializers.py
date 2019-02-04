"""serializers for user's tokens."""
from rest_framework import serializers
from oscar_accounts.models import Account


class AccountSerializer(serializers.ModelSerializer):
    account_type = serializers.SlugRelatedField(slug_field="name", read_only=True)
    package_name = serializers.SerializerMethodField()

    class Meta:
        model = Account
        exclude = ("code", "can_be_used_for_non_products", "primary_user",
                   "product_range", "secondary_users",)

    def get_package_name(self, obj):
        # last success full order
        order = obj.primary_user.orders.filter(status='Success').first()
        if order:
            return order.lines.first().product.title
