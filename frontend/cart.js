const rows = document.getElementById('rows');
const sum = document.getElementById('sum');
const msg = document.getElementById('msg');
const H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'};
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }

async function load() {
  const r = await fetch('/api/cart');
  if (r.status === 401) { location.href = '/login.html?next=/cart.html'; return; }   // authorization: login required
  const d = await r.json();
  rows.textContent = ''; sum.textContent = '';
  if (!d.items.length) { rows.appendChild(el('p', 'note', 'Your cart is empty. Add something from the shop!')); return; }
  for (const i of d.items) {
    const row = el('div', 'row');
    row.append(el('span', '', i.name), el('span', 'muted', 'x' + i.qty), el('b', '', '$' + (i.price * i.qty).toFixed(2)));
    const x = el('button', 'x', '\u2715');
    x.title = 'Remove';
    x.addEventListener('click', async () => { await fetch('/api/cart/' + i.id, {method: 'DELETE', headers: H}); load(); window.refreshNav(); });
    row.appendChild(x);
    rows.appendChild(row);
  }
  sum.appendChild(el('span', '', 'Total: $' + d.total.toFixed(2)));
  const pay = el('button', '', 'Checkout');
  pay.addEventListener('click', async () => {
    const c = await fetch('/api/checkout', {method: 'POST', headers: H, body: '{}'});
    const o = await c.json().catch(() => ({}));
    if (c.ok) { msg.className = 'formmsg ok'; msg.textContent = 'Order #' + o.order + ' placed. Total $' + o.total.toFixed(2) + '. Thank you!'; load(); window.refreshNav(); }
    else { msg.className = 'formmsg err'; msg.textContent = o.error || 'Checkout failed'; }
  });
  sum.appendChild(pay);
}
load();