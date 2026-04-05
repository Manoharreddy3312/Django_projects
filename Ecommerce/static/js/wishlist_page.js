(function () {
  const root = document.getElementById('wish-root');
  const loading = document.getElementById('wish-loading');

  async function load() {
    try {
      const data = await window.FlipMart.apiJson('/api/v1/wishlist/', { method: 'GET' });
      loading.remove();
      const items = data.results || data;
      if (!items.length) {
        root.innerHTML = '<p class="text-muted">Wishlist is empty.</p>';
        return;
      }
      root.innerHTML = items
        .map(
          (w) => `
      <div class="col-md-4">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <h3 class="h6">${w.product.name}</h3>
            <p class="text-primary mb-2">₹ ${w.product.price}</p>
            <a class="btn btn-sm btn-primary" href="/products/${w.product.slug}/">View</a>
            <button type="button" class="btn btn-sm btn-outline-danger ms-1 rm-w" data-id="${w.product.id}">Remove</button>
          </div>
        </div>
      </div>`
        )
        .join('');
      root.querySelectorAll('.rm-w').forEach((b) =>
        b.addEventListener('click', async () => {
          await window.FlipMart.toggleWishlist(b.dataset.id);
          load();
        })
      );
    } catch (e) {
      loading.innerHTML = '<p class="text-danger">Failed to load wishlist.</p>';
    }
  }
  load();
})();
