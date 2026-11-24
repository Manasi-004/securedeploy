const msg = document.getElementById('msg');
// Only allow redirects to paths on this site (prevents "open redirect" phishing links).
const wanted = new URLSearchParams(location.search).get('next') || '/';
const next = (wanted.startsWith('/') && !wanted.startsWith('//') && !wanted.includes('\\')) ? wanted : '/';

document.getElementById('show').addEventListener('change', e => {
  document.getElementById('p').type = e.target.checked ? 'text' : 'password';
});
document.getElementById('loginForm').addEventListener('submit', async e => {
  e.preventDefault();
  msg.className = 'formmsg'; msg.textContent = '';
  try {
    const r = await fetch('/api/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username: document.getElementById('u').value, password: document.getElementById('p').value})
    });
    const d = await r.json().catch(() => ({}));
    if (r.ok) { msg.className = 'formmsg ok'; msg.textContent = 'Welcome, ' + d.username + '!'; location.href = next; }
    else if (r.status === 403) { msg.className = 'formmsg err'; msg.textContent = 'Blocked by the web application firewall.'; }
    else { msg.className = 'formmsg err'; msg.textContent = d.error || 'Login failed'; }
  } catch { msg.className = 'formmsg err'; msg.textContent = 'Something went wrong.'; }
});