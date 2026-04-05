from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.models import BankDetail, Category, Product, ProductImage
from store.placeholder_images import category_banner, product_card, product_extra


CATEGORY_COLORS = [
    (13, 110, 253),
    (214, 51, 132),
    (25, 135, 84),
    (111, 66, 193),
    (253, 126, 20),
    (32, 201, 151),
]


class Command(BaseCommand):
    help = 'Create sample categories and products; attach generated PNG images (Pillow).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--images-only',
            action='store_true',
            help='Only fill missing category/product images (no new products).',
        )

    def handle(self, *args, **options):
        data = [
            ('Electronics', ['Smartphone X', 'Wireless Buds', 'USB-C Hub']),
            ('Fashion', ['Cotton Tee', 'Running Shoes', 'Leather Belt']),
            ('Home', ['Desk Lamp', 'Coffee Mug Set', 'Throw Blanket']),
        ]
        n_new = 0
        if not options['images_only']:
            for cat_name, products in data:
                cat, _ = Category.objects.get_or_create(
                    slug=slugify(cat_name),
                    defaults={'name': cat_name, 'description': f'{cat_name} deals'},
                )
                for pname in products:
                    slug = slugify(f'{cat_name}-{pname}')
                    p, created = Product.objects.get_or_create(
                        slug=slug,
                        defaults={
                            'category': cat,
                            'name': pname,
                            'description': f'Quality {pname}.',
                            'price': Decimal('999.00') + Decimal(n_new * 50),
                            'stock': 25,
                            'sku': f'SKU-{n_new}',
                        },
                    )
                    if created:
                        n_new += 1

        cats = list(Category.objects.all().order_by('id'))
        for i, cat in enumerate(cats):
            if cat.image:
                continue
            rgb = CATEGORY_COLORS[i % len(CATEGORY_COLORS)]
            cf = category_banner(cat.name, cat.slug, rgb)
            cat.image.save(cf.name, cf, save=True)
            self.stdout.write(f'  category image: {cat.slug}')

        products = list(Product.objects.all().select_related('category').order_by('id'))
        for i, p in enumerate(products):
            try:
                cat_idx = next(j for j, c in enumerate(cats) if c.pk == p.category_id)
            except StopIteration:
                cat_idx = i
            base_rgb = CATEGORY_COLORS[cat_idx % len(CATEGORY_COLORS)]
            rgb = tuple(max(0, min(255, c + (i * 11) % 55 - 20)) for c in base_rgb)

            if not p.main_image:
                cf = product_card(p.name, p.slug, rgb)
                p.main_image.save(cf.name, cf, save=True)
                self.stdout.write(f'  product main: {p.slug}')

            n_extra = p.images.count()
            for variant in range(n_extra, 2):
                ex = product_extra(p.slug, rgb, variant=variant)
                pi = ProductImage(product=p, sort_order=variant)
                pi.image.save(ex.name, ex, save=True)
            if n_extra < 2:
                self.stdout.write(f'  product gallery: {p.slug} (+{2 - n_extra})')

        if not BankDetail.objects.exists():
            BankDetail.objects.create(
                title='FlipMart collections',
                account_holder_name='FlipMart Demo Pvt Ltd',
                bank_name='State Bank of India',
                branch='Mumbai — Main branch',
                account_number='12345678901',
                ifsc_code='SBIN0001234',
                upi_id='flipmart.demo@upi',
                instructions=(
                    'Use your Order ID in the payment note / remarks. '
                    'After payment, submit UTR on the checkout page. '
                    'NEFT may take up to 24 hours.'
                ),
                is_active=True,
                sort_order=0,
            )
            self.stdout.write('  default bank details for manual transfer')

        msg = f'Seed done ({n_new} new products).' if not options['images_only'] else 'Images filled for existing catalog.'
        self.stdout.write(self.style.SUCCESS(msg))
