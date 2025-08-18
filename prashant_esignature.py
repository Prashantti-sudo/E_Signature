import streamlit as st
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5

# Streamlit page setup
st.set_page_config(page_title="🔐 Digital Signature Tool", page_icon="✍️", layout="centered")

st.title("🔐 Digital Signature Application")
st.write("Upload keys, data files, and create or verify digital signatures using RSA + SHA256.")

# Mode selection
mode = st.radio("Choose Operation", ["Sign Data", "Verify Signature"])

# Uploads
key_file = st.file_uploader("Upload Key File (.pem)", type=["pem"])
data_file = st.file_uploader("Upload Data File (any type)", type=None)

if mode == "Sign Data":
    if key_file and data_file:
        if st.button("Generate Signature"):
            try:
                key = RSA.importKey(key_file.read())
                data = data_file.read()

                h = SHA256.new(data)
                signer = PKCS1_v1_5.new(key)
                signature = signer.sign(h)

                st.success("✅ Signature generated successfully!")
                st.download_button("⬇️ Download Signature File",
                                   data=signature,
                                   file_name="signature.bin",
                                   mime="application/octet-stream")
            except Exception as e:
                st.error(f"Error generating signature: {e}")

elif mode == "Verify Signature":
    sig_file = st.file_uploader("Upload Signature File (.bin)", type=["bin"])
    if key_file and data_file and sig_file:
        if st.button("Verify Signature"):
            try:
                key = RSA.importKey(key_file.read())
                data = data_file.read()
                signature = sig_file.read()

                h = SHA256.new(data)
                verifier = PKCS1_v1_5.new(key)
                valid = verifier.verify(h, signature)

                if valid:
                    st.success("✅ Signature Verification Successful!")
                else:
                    st.error("❌ Verification Failed! Signature is not valid.")
            except Exception as e:
