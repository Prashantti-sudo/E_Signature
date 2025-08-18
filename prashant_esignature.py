import streamlit as st
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
import base64

st.set_page_config(page_title="Digital Signature App", page_icon="🔐")
st.title("🔐 Digital Signature App (RSA)")

# Sidebar selection
mode = st.sidebar.radio("Choose Mode", ["Generate Keys", "Sign Data", "Verify Signature"])

# Generate RSA Key Pair
if mode == "Generate Keys":
    st.subheader("🔑 Generate RSA Key Pair")
    if st.button("Generate Keys"):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()

        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        st.download_button("⬇️ Download Private Key", pem_private, "private_key.pem")
        st.download_button("⬇️ Download Public Key", pem_public, "public_key.pem")

# Sign Data
elif mode == "Sign Data":
    st.subheader("✍️ Sign Data")
    priv_key_file = st.file_uploader("Upload Private Key (.pem)", type=["pem"])
    data_file = st.file_uploader("Upload File to Sign", type=["txt", "pdf", "png", "jpg", "jpeg"])

    if priv_key_file and data_file:
        private_key = serialization.load_pem_private_key(
            priv_key_file.read(),
            password=None,
        )
        data = data_file.read()

        if st.button("Generate Signature"):
            signature = private_key.sign(
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            signature_b64 = base64.b64encode(signature)
            st.success("✅ Signature generated successfully!")
            st.code(signature_b64.decode(), language="bash")

            st.download_button("⬇️ Download Signature", signature, "signature.sig")

# Verify Signature
elif mode == "Verify Signature":
    st.subheader("🔎 Verify Signature")
    pub_key_file = st.file_uploader("Upload Public Key (.pem)", type=["pem"])
    data_file = st.file_uploader("Upload File", type=["txt", "pdf", "png", "jpg", "jpeg"])
    sig_file = st.file_uploader("Upload Signature File (.sig)", type=["sig"])

    if pub_key_file and data_file and sig_file:
        public_key = serialization.load_pem_public_key(pub_key_file.read())
        data = data_file.read()
        signature = sig_file.read()

        if st.button("Verify Signature"):
            try:
                public_key.verify(
                    signature,
                    data,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                st.success("✅ Signature is valid!")
            except InvalidSignature:
                st.error("❌ Verification failed! Invalid signature.")
