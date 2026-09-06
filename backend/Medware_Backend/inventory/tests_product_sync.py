"""Product and InventoryItem must mirror each other.

Orders reference products, not inventory items. While the sync ran one way
only, an item added straight to inventory had no product, so it could not be
ordered at all - the order form had nothing valid to send and the request
failed with the item simply refusing to work.
"""

from decimal import Decimal

from django.test import TestCase

from inventory.models import InventoryCategory, InventoryItem
from products.models import Product


class ProductToInventoryTests(TestCase):
    def test_saving_a_product_creates_its_inventory_item(self):
        product = Product.objects.create(name='Gloves', retail_price='3.00')

        item = InventoryItem.objects.get(product=product)

        self.assertEqual(item.name, 'Gloves')

    def test_saving_a_product_does_not_create_a_second_item(self):
        product = Product.objects.create(name='Gloves', retail_price='3.00')

        product.name = 'Gloves L'
        product.save()

        self.assertEqual(InventoryItem.objects.filter(product=product).count(), 1)
        self.assertEqual(InventoryItem.objects.get(product=product).name, 'Gloves L')


class InventoryToProductTests(TestCase):
    def setUp(self):
        self.category = InventoryCategory.objects.create(name='Dressings')

    def test_an_inventory_only_item_gets_a_product(self):
        """The bug this closes: no product meant the item could not be ordered."""
        item = InventoryItem.objects.create(
            name='Tar', category=self.category,
            whole_price=Decimal('2.00'), retail_price=Decimal('5.00'))

        item.refresh_from_db()
        self.assertIsNotNone(item.product_id)
        self.assertEqual(item.product.name, 'Tar')
        self.assertEqual(item.product.retail_price, Decimal('5.00'))

    def test_it_creates_exactly_one_item_and_one_product(self):
        """The two syncs must not bounce off each other.

        Creating the product fires the product->inventory handler, which cannot
        see the link yet; without the guard it would create a second item.
        """
        InventoryItem.objects.create(name='Tar', category=self.category)

        self.assertEqual(InventoryItem.objects.filter(name='Tar').count(), 1)
        self.assertEqual(Product.objects.filter(name='Tar').count(), 1)

    def test_the_new_item_keeps_its_own_category(self):
        """The product->inventory handler defaults to 'Uncategorized'. If the
        round trip reached it, the item would lose the category it was given."""
        item = InventoryItem.objects.create(name='Tar', category=self.category)

        item.refresh_from_db()
        self.assertEqual(item.category, self.category)

    def test_editing_the_item_updates_its_product(self):
        item = InventoryItem.objects.create(name='Tar', category=self.category)
        item.refresh_from_db()

        item.name = 'Tar 500ml'
        item.retail_price = Decimal('7.50')
        item.save()

        product = Product.objects.get(pk=item.product_id)
        self.assertEqual(product.name, 'Tar 500ml')
        self.assertEqual(product.retail_price, Decimal('7.50'))

    def test_an_item_that_already_has_a_product_gains_no_second_one(self):
        product = Product.objects.create(name='Gloves', retail_price='3.00')
        before = Product.objects.count()

        item = InventoryItem.objects.get(product=product)
        item.sku = 'GL-1'
        item.save()

        self.assertEqual(Product.objects.count(), before)

    def test_every_inventory_item_is_orderable(self):
        """What the order form actually depends on: a product id to send."""
        InventoryItem.objects.create(name='Tar', category=self.category)
        Product.objects.create(name='Gloves', retail_price='3.00')

        self.assertFalse(
            InventoryItem.objects.filter(product__isnull=True).exists(),
            'An item with no product cannot be ordered - the order form has no '
            'valid product id to send.')
