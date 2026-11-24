const grid = document.getElementById('grid');
const msg = document.getElementById('msg');
const toastEl = document.getElementById('toast');
const icons = {widget: '\u{1F527}', gadget: '\u{1F4F1}', gizmo: '\u{1F9E9}', headphones: '\u{1F3A7}',
  'smart watch': '\u231A', backpack: '\u{1F392}', keyboard: '\u2328\uFE0F', sunglasses: '\u{1F576}\uFE0F'};
let toastTimer;

// el() sets text with textContent only (never innerHTML), so data cannot inject markup.
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}
function toast(text) {
  toastEl.textContent = text;
  toastEl.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove('show'), 1600);
}
async function addToCart(item) {
  const r = await fetch('/api/cart', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'},
    body: JSON.stringify({product_id: item.id})
  });
  if (r.status === 401) { location.href = '/login.html?next=/'; return; }   // must be logged in
  if (!r.ok) { toast('Could not add to cart'); return; }
  toast(item.name + ' added to cart');
  window.refreshNav();
}
async function load(q) {
  msg.textContent = '';
  try {
    const r = await fetch('/api/products?q=' + encodeURIComponent(q));
    if (r.status === 403) { msg.textContent = 'Request blocked by the web application firewall.'; grid.textContent = ''; return; }
    if (!r.ok) throw new Error();
    const items = await r.json();
    grid.textContent = '';
    if (!items.length) { msg.textContent = 'No products found.'; return; }
    for (const i of items) {
      const card = el('article', 'card');
      card.appendChild(el('div', 'pic', icons[i.name.toLowerCase()] || '\u{1F6CD}\uFE0F'));
      const info = el('div', 'info');
      info.appendChild(el('h3', '', i.name));
      info.appendChild(el('p', 'desc', i.description));
      info.appendChild(el('div', 'price', '$' + i.price.toFixed(2)));
      const btn = el('button', '', 'Add to cart');
      btn.addEventListener('click', () => addToCart(i));
      info.appendChild(btn);
      card.appendChild(info);
      grid.appendChild(card);
    }
  } catch { msg.textContent = 'Something went wrong. Please try again.'; }
}
document.getElementById('searchForm').addEventListener('submit', e => {
  e.preventDefault();
  load(document.getElementById('q').value);
});
load('');