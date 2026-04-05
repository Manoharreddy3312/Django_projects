def cart_count(request):
    if not request.user.is_authenticated:
        return {'cart_item_count': 0}
    from .models import Cart

    cart, _ = Cart.objects.get_or_create(user=request.user)
    n = sum(i.quantity for i in cart.items.all())
    return {'cart_item_count': n}
