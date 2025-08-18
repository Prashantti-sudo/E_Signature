import streamlit as st
from Crypto.Util.number import getPrime
from random import randint
from hashlib import sha1

# Hash of message in SHA1
def hash_function(message):
    hashed = sha1(message.encode("UTF-8")).hexdigest()
    return hashed

# Modular Multiplicative Inverse
def mod_inverse(a, m):
    a = a % m
    for x in range(1, m):
        if (a * x) % m == 1:
            return x
    return 1

# Global parameters: q, p, g
def parameter_generation(h):
    q = getPrime(5)
    p = getPrime(10)

    while (p - 1) % q != 0:
        p = getPrime(10)
        q = getPrime(5)

    g = pow(h, int((p - 1) / q), p)
    if g == 1:
        g = pow(h + 1, int((p - 1) / q), p)

    return p, q, g

# Per-user key pair
def per_user_key(p, q, g):
    x = randint(1, q - 1)  # private key
    y = pow(g, x, p)      # public key
    return x, y

# Signing function
def signature(text, p, q, g, x):
    hash_component = hash_function(text)
    r, s = 0, 0
    while s == 0 or r == 0:
        k = randint(1, q - 1)
        r = (pow(g, k, p)) % q
        i = mod_inverse(k, q)
        hashed = int(hash_component, 16)
        s = (i * (hashed + (x * r))) % q
    return r, s, k, hash_component

# Verification function
def verification(text, p, q, g, r, s, y):
    hash_component = hash_function(text)
    w = mod_inverse(s, q)
    hashed = int(hash_component, 16)
    u1 = (hashed * w) % q
    u2 = (r * w) % q
    v = ((pow(g, u1, p) * pow(y, u2, p)) % p) % q
    return v == r, hash_component, u1, u2, v, w

# ---------------- STREAMLIT APP -----------------
st.title("🔐 Digital Signature Algorithm (DSA) Demo")

st.sidebar.header("DSA Parameters")
h = st.sidebar.number_input("Enter integer h (1 < h < p-1):", min_value=2, value=5)

if st.sidebar.button("Generate Parameters"):
    p, q, g = parameter_generation(h)
    st.session_state["p"], st.session_state["q"], st.session_state["g"] = p, q, g
    st.success(f"Generated Parameters → p: {p}, q: {q}, g: {g}")

if "p" in st.session_state:
    p, q, g = st.session_state["p"], st.session_state["q"], st.session_state["g"]
    st.subheader("🔑 Key Generation")
    if st.button("Generate Keys"):
        x, y = per_user_key(p, q, g)
        st.session_state["x"], st.session_state["y"] = x, y
        st.info(f"Private Key (x): {x}")
        st.success(f"Public Key (y): {y}")

if "x" in st.session_state:
    st.subheader("✍️ Sign Document")
    text_to_sign = st.text_area("Enter message/document to sign")
    if st.button("Sign Message") and text_to_sign:
        r, s, k, hash_sent = signature(text_to_sign, p, q, g, st.session_state["x"])
        st.session_state["r"], st.session_state["s"], st.session_state["k"] = r, s, k
        st.session_state["hash_sent"] = hash_sent
        st.write("**Hash (SHA1):**", hash_sent)
        st.write(f"r: {r}, s: {s}, k: {k}")

if "r" in st.session_state:
    st.subheader("✅ Verify Signature")
    text_to_verify = st.text_area("Enter message/document to verify")
    if st.button("Verify Signature") and text_to_verify:
        valid, hash_recv, u1, u2, v, w = verification(
            text_to_verify, p, q, g,
            st.session_state["r"],
            st.session_state["s"],
            st.session_state["y"]
        )
        st.write("**Hash (Received):**", hash_recv)
        st.write(f"w: {w}, u1: {u1}, u2: {u2}, v: {v}")
        if valid:
            st.success("The signature is VALID ✅")
        else:
            st.error("The signature is INVALID ❌")
