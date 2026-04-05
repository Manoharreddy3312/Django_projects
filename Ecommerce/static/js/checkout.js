(function () {
  let addresses = [];
  let selectedId = null;
  let lastBankOrderId = null;
  const addrList = document.getElementById('addr-list');
  const payBtn = document.getElementById('pay-btn');
  const debug = document.getElementById('pay-debug');
  const bankPanel = document.getElementById('bank-panel');
  const bankBody = document.getElementById('bank-details-body');
  const bankUtrBlock = document.getElementById('bank-utr-block');
  const bankUtr = document.getElementById('bank-utr');
  const bankSubmitRef = document.getElementById('bank-submit-ref');
  const hintRz = document.getElementById('pay-hint-rz');
  const hintBank = document.getElementById('pay-hint-bank');

  function paymentMethod() {
    const r = document.querySelector('input[name="pay-method"]:checked');
    return r ? r.value : 'razorpay';
  }

  document.querySelectorAll('input[name="pay-method"]').forEach((el) => {
    el.addEventListener('change', () => {
      const m = paymentMethod();
      const bank = m === 'bank_transfer';
      bankPanel.classList.toggle('d-none', !bank);
      hintRz.classList.toggle('d-none', bank);
      hintBank.classList.toggle('d-none', !bank);
      bankUtrBlock.classList.add('d-none');
      lastBankOrderId = null;
      payBtn.textContent = bank ? 'Place order & show bank details' : 'Pay with Razorpay';
    });
  });

  function renderAddresses() {
    if (!addrList) return;
    if (!addresses.length) {
      addrList.innerHTML = '<p class="text-muted small">No saved addresses.</p>';
      return;
    }
    addrList.innerHTML = addresses
      .map(
        (a) => `
      <div class="form-check border rounded p-2 mb-2">
        <input class="form-check-input addr-pick" type="radio" name="addr" id="a${a.id}" value="${a.id}">
        <label class="form-check-label" for="a${a.id}">${a.full_name}, ${a.city} — ${a.phone}</label>
      </div>`
      )
      .join('');
    addrList.querySelectorAll('.addr-pick').forEach((r) => {
      r.addEventListener('change', () => {
        selectedId = parseInt(r.value, 10);
        payBtn.disabled = !selectedId;
      });
    });
  }

  async function refreshAddresses() {
    const data = await window.FlipMart.apiJson('/api/v1/addresses/', { method: 'GET' });
    addresses = data.results || data;
    renderAddresses();
  }

  function renderBankDetails(banks, order) {
    const amount = order && order.total != null ? order.total : '';
    let html = '';
    if (amount !== '') {
      html += `<p class="fw-bold">Amount to pay: ₹ ${amount} <span class="text-muted small">(Order #${order.id})</span></p>`;
    }
    (banks || []).forEach((b) => {
      html += `<div class="border rounded p-3 mb-3 bg-light">
        <div class="fw-semibold">${b.title}</div>
        <div class="small mt-2"><strong>Account name:</strong> ${b.account_holder_name}</div>
        <div class="small"><strong>Bank:</strong> ${b.bank_name}${b.branch ? ' — ' + b.branch : ''}</div>
        <div class="small"><strong>Account no.:</strong> <code>${b.account_number}</code></div>
        <div class="small"><strong>IFSC:</strong> <code>${b.ifsc_code}</code></div>
        ${b.upi_id ? `<div class="small"><strong>UPI:</strong> <code>${b.upi_id}</code></div>` : ''}
        ${b.instructions ? `<div class="small text-muted mt-2">${b.instructions}</div>` : ''}
      </div>`;
    });
    bankBody.innerHTML = html || '<p class="text-danger">No bank details configured.</p>';
  }

  document.getElementById('addr-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = Object.fromEntries(fd.entries());
    try {
      await window.FlipMart.apiJson('/api/v1/addresses/', { method: 'POST', body: JSON.stringify(body) });
      window.FlipMart.toast('Address saved');
      e.target.reset();
      await refreshAddresses();
    } catch (err) {
      window.FlipMart.toast(err.message, true);
    }
  });

  payBtn?.addEventListener('click', async () => {
    if (!selectedId) return;
    const method = paymentMethod();
    payBtn.disabled = true;
    try {
      const res = await window.FlipMart.apiJson('/api/v1/orders/checkout/', {
        method: 'POST',
        body: JSON.stringify({ address_id: selectedId, payment_method: method }),
      });
      const order = res.order;

      if (method === 'bank_transfer') {
        renderBankDetails(res.bank_details, order);
        lastBankOrderId = order.id;
        bankUtrBlock.classList.remove('d-none');
        bankPanel.classList.remove('d-none');
        window.FlipMart.toast('Transfer the amount, then submit your UTR');
        payBtn.disabled = false;
        return;
      }

      const rz = res.razorpay;
      if (!rz || !rz.order_id) {
        if (debug) {
          debug.textContent = JSON.stringify(res, null, 2);
          debug.classList.remove('d-none');
        }
        window.FlipMart.toast(res.detail || 'Configure Razorpay keys or check response', true);
        payBtn.disabled = false;
        return;
      }
      const options = {
        key: rz.key_id,
        amount: rz.amount,
        currency: rz.currency,
        name: 'FlipMart',
        description: 'Order #' + order.id,
        order_id: rz.order_id,
        handler: async function (response) {
          try {
            await window.FlipMart.apiJson('/api/v1/payments/verify/', {
              method: 'POST',
              body: JSON.stringify({
                order_id: order.id,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              }),
            });
            window.FlipMart.toast('Payment successful');
            window.location.href = '/orders/' + order.id + '/';
          } catch (err) {
            window.FlipMart.toast(err.message, true);
          }
        },
        modal: { ondismiss: function () { payBtn.disabled = false; } },
      };
      const rzp = new Razorpay(options);
      rzp.open();
    } catch (err) {
      window.FlipMart.toast(err.message, true);
      payBtn.disabled = false;
    }
  });

  bankSubmitRef?.addEventListener('click', async () => {
    const ref = (bankUtr && bankUtr.value) ? bankUtr.value.trim() : '';
    if (!lastBankOrderId) {
      window.FlipMart.toast('Place a bank-transfer order first', true);
      return;
    }
    if (ref.length < 6) {
      window.FlipMart.toast('Enter a valid UTR / reference (min 6 characters)', true);
      return;
    }
    try {
      await window.FlipMart.apiJson('/api/v1/payments/bank-reference/', {
        method: 'POST',
        body: JSON.stringify({ order_id: lastBankOrderId, bank_reference: ref }),
      });
      window.FlipMart.toast('Reference submitted — we will verify shortly');
      window.location.href = '/orders/' + lastBankOrderId + '/';
    } catch (err) {
      window.FlipMart.toast(err.message, true);
    }
  });

  refreshAddresses().catch(() => {
    if (addrList) addrList.innerHTML = '<p class="text-danger">Load addresses failed.</p>';
  });
})();
