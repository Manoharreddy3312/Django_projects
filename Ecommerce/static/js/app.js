(function () {
  function getCookie(name) {
    const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? decodeURIComponent(v[2]) : null;
  }

  function getCsrfToken() {
    const el = document.querySelector('#flipmart-csrf-store input[name="csrfmiddlewaretoken"]');
    const fromInput = el && el.value;
    return fromInput || getCookie('csrftoken') || window.FLIPMART_CSRF || '';
  }

  function toast(msg, isError) {
    const el = document.getElementById('app-toast');
    const body = document.getElementById('app-toast-body');
    if (!el || !body) {
      alert(msg);
      return;
    }
    body.textContent = msg;
    el.classList.toggle('text-bg-danger', !!isError);
    el.classList.toggle('text-bg-dark', !isError);
    const t = bootstrap.Toast.getOrCreateInstance(el);
    t.show();
  }

  function showPageSpinner(show) {
    const s = document.getElementById('page-spinner');
    if (s) s.classList.toggle('d-none', !show);
  }

  async function apiJson(url, opts) {
    const token = getCsrfToken();
    const headers = Object.assign(
      {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        'X-CSRFToken': token,
        'X-Requested-With': 'XMLHttpRequest',
      },
      (opts && opts.headers) || {}
    );
    const r = await fetch(url, Object.assign({ credentials: 'same-origin' }, opts, { headers }));
    let data = {};
    try {
      data = await r.json();
    } catch (e) {}
    if (!r.ok) {
      const msg =
        data.detail ||
        data.error ||
        (data.ok === false && data.error) ||
        (typeof data === 'object' && Object.keys(data).length ? JSON.stringify(data) : '') ||
        r.statusText;
      const err = new Error(msg || 'Request failed');
      err.status = r.status;
      throw err;
    }
    return data;
  }

  async function addToCart(productId, quantity) {
    showPageSpinner(true);
    try {
      await apiJson('/api/v1/cart/items/', {
        method: 'POST',
        body: JSON.stringify({ product_id: productId, quantity: parseInt(quantity, 10) || 1 }),
      });
      toast('Added to cart');
      const badge = document.getElementById('nav-cart-count');
      if (badge) {
        const n = parseInt(badge.textContent, 10) || 0;
        badge.textContent = n + (parseInt(quantity, 10) || 1);
      }
    } catch (e) {
      if (e.status === 403) {
        toast('Please log in to add to cart', true);
        const m = document.getElementById('authModal');
        if (m) new bootstrap.Modal(m).show();
      } else toast(e.message, true);
    } finally {
      showPageSpinner(false);
    }
  }

  async function toggleWishlist(productId) {
    showPageSpinner(true);
    try {
      const d = await apiJson('/api/v1/wishlist/toggle/', {
        method: 'POST',
        body: JSON.stringify({ product_id: productId }),
      });
      toast(d.in_wishlist ? 'Added to wishlist' : 'Removed from wishlist');
    } catch (e) {
      if (e.status === 403) {
        toast('Please log in', true);
        const m = document.getElementById('authModal');
        if (m) new bootstrap.Modal(m).show();
      } else toast(e.message, true);
    } finally {
      showPageSpinner(false);
    }
  }

  /* Search suggestions */
  let searchTimer;
  const input = document.getElementById('search-input');
  const sug = document.getElementById('search-suggestions');
  if (input && sug) {
    input.addEventListener('input', function () {
      clearTimeout(searchTimer);
      const q = this.value.trim();
      if (q.length < 2) {
        sug.classList.add('d-none');
        sug.innerHTML = '';
        return;
      }
      searchTimer = setTimeout(async () => {
        try {
          const u = new URL('/api/v1/products/', window.location.origin);
          u.searchParams.set('search', q);
          u.searchParams.set('page_size', '8');
          const r = await fetch(u, { headers: { Accept: 'application/json' } });
          const data = await r.json();
          const items = data.results || data;
          sug.innerHTML = (Array.isArray(items) ? items : [])
            .map(
              (p) =>
                `<a class="list-group-item list-group-item-action" href="/products/${p.slug}/">${p.name}</a>`
            )
            .join('');
          sug.classList.toggle('d-none', !sug.innerHTML);
        } catch (e) {
          sug.classList.add('d-none');
        }
      }, 250);
    });
    document.addEventListener('click', function (e) {
      if (!sug.contains(e.target) && e.target !== input) sug.classList.add('d-none');
    });
  }

  /* OTP modal */
  const sendOtp = document.getElementById('otp-send-btn');
  const verifyOtp = document.getElementById('otp-verify-btn');
  if (sendOtp) {
    sendOtp.addEventListener('click', async () => {
      const idf = document.getElementById('otp-identifier').value.trim();
      const sp = document.getElementById('otp-spinner');
      if (!idf) {
        toast('Enter your email or mobile number', true);
        return;
      }
      if (!getCsrfToken()) {
        toast('Security token missing — refresh the page and try again', true);
        return;
      }
      sp && sp.classList.remove('d-none');
      try {
        await apiJson('/accounts/api/otp/request/', {
          method: 'POST',
          body: JSON.stringify({ identifier: idf }),
        });
        toast('OTP sent (check email or SMS)');
      } catch (e) {
        toast(e.message, true);
      } finally {
        sp && sp.classList.add('d-none');
      }
    });
  }
  if (verifyOtp) {
    verifyOtp.addEventListener('click', async () => {
      const idf = document.getElementById('otp-identifier').value.trim();
      const code = document.getElementById('otp-code').value.trim();
      const next = window.location.pathname + window.location.search;
      if (!getCsrfToken()) {
        toast('Security token missing — refresh the page and try again', true);
        return;
      }
      try {
        const d = await apiJson('/accounts/api/otp/verify/', {
          method: 'POST',
          body: JSON.stringify({ identifier: idf, code, next }),
        });
        if (d.redirect) window.location.href = d.redirect;
      } catch (e) {
        toast(e.message, true);
      }
    });
  }

  window.FlipMart = { toast, apiJson, addToCart, toggleWishlist, getCookie, getCsrfToken };
})();
