import hashlib
import json
import os
import re
import time
from datetime import timedelta
from functools import wraps

import psycopg2
import psycopg2.errors
from flask import Flask, jsonify, request, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,          # JavaScript cannot read the cookie
    SESSION_COOKIE_SAMESITE="Lax",         # not sent on cross-site POSTs
    # Set COOKIE_SECURE=true once the site is served over HTTPS.
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    MAX_CONTENT_LENGTH=16 * 1024,
)
USER_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")


def db_conn():
    return psycopg2.connect(host=os.environ["DB_HOST"], dbname=os.environ["DB_NAME"],
                            user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"])


def client_ip():
    # Behind a load balancer the LAST X-Forwarded-For entry is the real client.
    xff = request.headers.get("X-Forwarded-For", "")
    return xff.split(",")[-1].strip() if xff else request.remote_addr


def audit(event, username=None, **fields):
    ip = client_ip()
    print(json.dumps({"ts": time.time(), "event": event, "src_ip": ip,
                      "username": username, **fields}), flush=True)
    try:
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO security_events (event, src_ip, username, detail) VALUES (%s,%s,%s,%s)",
                        (event, ip, (username or "")[:100], json.dumps(fields)[:500]))
    except Exception:
        pass


def login_required(fn):
    """AUTHENTICATION check: no valid session -> 401.
    For anything that changes data, also require a custom header. Browsers will not add a
    custom header to a cross-site form post, so this blocks CSRF (forged requests)."""
    @wraps(fn)
    def wrapper(*a, **kw):
        if "uid" not in session:
            return jsonify(error="Please log in"), 401
        if request.method != "GET" and request.headers.get("X-Requested-With") != "fetch":
            return jsonify(error="Bad request"), 400
        return fn(*a, **kw)
    return wrapper


def start_session(uid, username, role):
    session.clear()                 # new session on login prevents session fixation
    session.permanent = True
    session.update(uid=uid, user=username, role=role)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/api/products")
def products():
    q = request.args.get("q", "")[:100]
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, description, price FROM products WHERE name ILIKE %s ORDER BY id",
                    (f"%{q}%",))
        rows = cur.fetchall()
    return jsonify([{"id": r[0], "name": r[1], "description": r[2], "price": float(r[3])} for r in rows])


# ---------------------------------------------------------------- accounts
@app.post("/api/signup")
def signup():
    # LAB NOTE: passwords are stored as unsalted MD5, the same deliberate weakness as login.
    # The hardened fix is werkzeug.security.generate_password_hash (salted scrypt).
    body = request.get_json(silent=True) or {}
    user = str(body.get("username", ""))
    pw = str(body.get("password", ""))[:200]
    if not USER_RE.match(user):
        return jsonify(error="Username must be 3-30 letters, numbers or underscores"), 400
    if len(pw) < 6:
        return jsonify(error="Password must be at least 6 characters"), 400
    try:
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, role",
                        (user, hashlib.md5(pw.encode()).hexdigest()))  # nosec - intentional weakness
            uid, role = cur.fetchone()
    except psycopg2.errors.UniqueViolation:
        audit("signup_failed", username=user, reason="exists")
        return jsonify(error="That username is already taken"), 409
    audit("signup", username=user)
    start_session(uid, user, role)
    return jsonify(ok=True, username=user), 201


@app.post("/api/login")
def login():
    # ======================================================================
    # DELIBERATELY WEAK - FOR TESTING ONLY. NEVER COPY THIS INTO A REAL APP.
    #   1. No lockout or rate limit in the code (the WAF rate rule is the control).
    #   2. Passwords hashed with unsalted MD5 (easily cracked).
    #   3. SQL INJECTION (CWE-89): query built with string concatenation.
    #      This allows a full authentication bypass, e.g. username:
    #      ' OR '1'='1' --   with any password.
    # ======================================================================
    body = request.get_json(silent=True) or {}
    user = str(body.get("username", ""))[:200]
    pw = str(body.get("password", ""))[:200]
    pw_hash = hashlib.md5(pw.encode()).hexdigest()  # intentional weakness
    # VULNERABLE: both values glued directly into the SQL text, not parameterized.
    query = ("SELECT id, username, role FROM users WHERE username = '" + user +
              "' AND password_hash = '" + pw_hash + "'")
    try:
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
    except Exception as exc:
        audit("login_error", username=user, error=str(exc)[:200])
        return jsonify(error=str(exc)), 500
    if row is None:
        audit("login_failed", username=user)
        return jsonify(error="Invalid credentials"), 401
    audit("login_success", username=row[1])
    start_session(row[0], row[1], row[2])
    return jsonify(ok=True, username=row[1])

@app.post("/api/logout")
@login_required
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/me")
@login_required
def me():
    return jsonify(username=session["user"], role=session["role"])


# ---------------------------------------------------------------- cart (AUTHORIZATION)
# Every query below filters by session["uid"], taken from the signed session and NEVER from
# the request. A user therefore cannot read or change another user's cart.
@app.get("/api/cart")
@login_required
def cart():
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT p.id, p.name, p.price, c.qty FROM cart_items c "
                    "JOIN products p ON p.id = c.product_id WHERE c.user_id = %s ORDER BY p.id",
                    (session["uid"],))
        items = [{"id": r[0], "name": r[1], "price": float(r[2]), "qty": r[3]} for r in cur.fetchall()]
    return jsonify(items=items, total=round(sum(i["price"] * i["qty"] for i in items), 2))


@app.post("/api/cart")
@login_required
def cart_add():
    body = request.get_json(silent=True) or {}
    try:
        pid = int(body.get("product_id"))
    except (TypeError, ValueError):
        return jsonify(error="Invalid product"), 400
    try:
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO cart_items (user_id, product_id, qty) VALUES (%s, %s, 1) "
                        "ON CONFLICT (user_id, product_id) DO UPDATE SET qty = LEAST(cart_items.qty + 1, 10)",
                        (session["uid"], pid))
    except psycopg2.errors.ForeignKeyViolation:
        return jsonify(error="No such product"), 404
    return jsonify(ok=True)


@app.delete("/api/cart/<int:pid>")
@login_required
def cart_remove(pid):
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM cart_items WHERE user_id = %s AND product_id = %s", (session["uid"], pid))
    return jsonify(ok=True)


@app.post("/api/checkout")
@login_required
def checkout():
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(p.price * c.qty), 0), COUNT(*) FROM cart_items c "
                    "JOIN products p ON p.id = c.product_id WHERE c.user_id = %s", (session["uid"],))
        total, n = cur.fetchone()
        if n == 0:
            return jsonify(error="Your cart is empty"), 400
        cur.execute("INSERT INTO orders (user_id, total) VALUES (%s, %s) RETURNING id", (session["uid"], total))
        order_id = cur.fetchone()[0]
        cur.execute("DELETE FROM cart_items WHERE user_id = %s", (session["uid"],))
    audit("order_placed", username=session["user"], order=order_id)
    return jsonify(ok=True, order=order_id, total=float(total))

    

