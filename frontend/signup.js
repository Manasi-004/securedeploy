const msg = document.getElementById('msg');
document.getElementById('signupForm').addEventListener('submit', async e => {
  e.preventDefault();
  msg.className = 'formmsg'; msg.textContent = '';
  const pw = document.getElementById('p').value;
  if (pw !== document.getElementById('p2').value) { msg.className = 'formmsg err'; msg.textContent = 'Passwords do not match.'; return; }
  try {
    const r = await fetch('/api/signup', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username: document.getElementById('u').value, password: pw})
    });
    const d = await r.json().catch(() => ({}));
    if (r.ok) { location.href = '/'; }
    else if (r.status === 403) { msg.className = 'formmsg err'; msg.textContent = 'Blocked by the web application firewall.'; }
    else { msg.className = 'formmsg err'; msg.textContent = d.error || 'Sign up failed'; }
  } catch { msg.className = 'formmsg err'; msg.textContent = 'Something went wrong.'; }
});