(function () {
  const root = document.getElementById('cart-content');
  const loading = document.getElementById('cart-loading');

  function render(cart) {
    loading.classList.add('d-none');
    root.classList.remove('d-none');
    if (!cart.items || !cart.items.length) {
      root.innerHTML = '<p class="text-muted mb-0">Your cart is empty.</p>';
      document.getElementById('checkout-link')?.classList.add('disabled');
      return;
    }
    let html =
      '<table class="table mb-0"><thead><tr><th>Product</th><th>Qty</th><th></th></tr></thead><tbody>';
    cart.items.forEach((it) => {
      html += `<tr>
        <td>${it.product.name}<div class="small text-muted">₹ ${it.product.price}</div></td>
        <td style="width:140px">
          <input type="number" class="form-control form-control-sm cart-qty" data-id="${it.id}" value="${it.quantity}" min="1">
        </td>
        <td><button type="button" class="btn btn-sm btn-outline-danger cart-remove" data-id="${it.id}">Remove</button></td>
      </tr>`;
    });
    html += '</tbody></table><p class="mt-3 mb-0 fw-bold">Total: ₹ ' + cart.total + '</p>';
    root.innerHTML = html;
    root.querySelectorAll('.cart-qty').forEach((inp) => {
      inp.addEventListener('change', async () => {
        const id = inp.dataset.id;
        const q = parseInt(inp.value, 10);
        try {
          await window.FlipMart.apiJson('/api/v1/cart/items/' + id + '/', {
            method: 'PATCH',
            body: JSON.stringify({ quantity: q }),
          });
          load();
        } catch (e) {
          window.FlipMart.toast(e.message, true);
        }
      });
    });
    root.querySelectorAll('.cart-remove').forEach((btn) => {
      btn.addEventListener('click', async () => {
        try {
          await window.FlipMart.apiJson('/api/v1/cart/items/' + btn.dataset.id + '/remove/', {
            method: 'DELETE',
          });
          load();
        } catch (e) {
          window.FlipMart.toast(e.message, true);
        }
      });
    });
  }

  async function load() {
    try {
      const cart = await window.FlipMart.apiJson('/api/v1/cart/', { method: 'GET' });
      render(cart);
    } catch (e) {
      loading.innerHTML = '<p class="text-danger">Could not load cart.</p>';
    }
  }

  load();
})();
