const msg = document.getElementById('msg');
document.getElementById('labLoginForm').addEventListener('submit', async e => {
  e.preventDefault();
  msg.className = 'formmsg'; msg.textContent = '';
  try {
    const r = await fetch('/api/lab/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username: document.getElementById('u').value, password: document.getElementById('p').value})
    });
    const d = await r.json().catch(() => ({}));
    if (r.ok) { msg.className = 'formmsg ok'; msg.textContent = 'Logged in as ' + d.username + ' - ' + d.note; }
    else { msg.className = 'formmsg err'; msg.textContent = d.error || 'Login failed'; }
  } catch { msg.className = 'formmsg err'; msg.textContent = 'Something went wrong.'; }
});