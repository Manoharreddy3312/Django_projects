from django.urls import path

from . import views

app_name = 'store'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('cart/', views.CartPageView.as_view(), name='cart'),
    path('wishlist/', views.WishlistPageView.as_view(), name='wishlist'),
    path('checkout/', views.CheckoutPageView.as_view(), name='checkout'),
    path('orders/', views.OrdersPageView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderDetailPageView.as_view(), name='order_detail'),
]
