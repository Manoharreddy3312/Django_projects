from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView, TemplateView, View

from .models import Category, Order, Product


class HomeView(TemplateView):
    template_name = 'store/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['featured'] = Product.objects.filter(is_active=True)[:8]
        ctx['categories'] = Category.objects.filter(is_active=True)[:12]
        return ctx


class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related('category')
        q = self.request.GET.get('q')
        cat = self.request.GET.get('category')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q))
        if cat:
            qs = qs.filter(category__slug=cat)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.filter(is_active=True)
        ctx['current_cat'] = self.request.GET.get('category', '')
        ctx['search_q'] = self.request.GET.get('q', '')
        return ctx


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category').prefetch_related(
            'images', 'reviews__user'
        )


class CartPageView(LoginRequiredMixin, TemplateView):
    template_name = 'store/cart.html'


class WishlistPageView(LoginRequiredMixin, TemplateView):
    template_name = 'store/wishlist.html'


class CheckoutPageView(LoginRequiredMixin, TemplateView):
    template_name = 'store/checkout.html'


class OrdersPageView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'store/orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailPageView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'store/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product', 'payment')

    def get_context_data(self, **kwargs):
        from .tracking import compute_tracking_display, refresh_order_tracking

        ctx = super().get_context_data(**kwargs)
        order = self.object
        refresh_order_tracking(order, send_mail_flag=True)
        order.refresh_from_db()
        ctx['tracking'] = compute_tracking_display(order)
        return ctx
