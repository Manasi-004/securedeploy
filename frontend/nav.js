// Builds the top-right menu. Shows Login/Sign up when logged out, and Hi/Cart/Logout when logged in.
async function renderNav() {
  const nav = document.getElementById('nav');
  let me = null, count = 0;
  try { const r = await fetch('/api/me'); if (r.ok) me = await r.json(); } catch {}
  if (me) {
    try { const c = await (await fetch('/api/cart')).json(); count = c.items.reduce((n, i) => n + i.qty, 0); } catch {}
  }
  const link = (text, href, cls) => { const a = document.createElement('a'); a.href = href; a.textContent = text; if (cls) a.className = cls; return a; };
  nav.textContent = '';
  nav.appendChild(link('Shop', '/'));
  nav.appendChild(link('Cart (' + count + ')', '/cart.html', 'pill'));
  if (me) {
    const hi = document.createElement('span'); hi.className = 'hi'; hi.textContent = 'Hi, ' + me.username;
    const out = document.createElement('button'); out.className = 'ghost'; out.textContent = 'Logout';
    out.addEventListener('click', async () => {
      await fetch('/api/logout', {method: 'POST', headers: {'X-Requested-With': 'fetch'}});
      location.href = '/';
    });
    nav.append(hi, out);
  } else {
    nav.appendChild(link('Login', '/login.html'));
    nav.appendChild(link('Sign up', '/signup.html', 'pill primary'));
  }
}
window.refreshNav = renderNav;
renderNav();