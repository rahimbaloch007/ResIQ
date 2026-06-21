import streamlit as st
import hashlib


def hash_password(password):
    """Simple SHA-256 hashing for password storage."""
    return hashlib.sha256(password.encode()).hexdigest()


def check_login(username, password):
    """
    Validates username/password against credentials
    stored in Streamlit secrets (st.secrets).

    Secrets format expected in .streamlit/secrets.toml:
    [credentials]
    rahim = "hashed_password_here"
    ppl_panel = "hashed_password_here"
    """
    if "credentials" not in st.secrets:
        return False

    stored_hash = st.secrets["credentials"].get(username)
    if stored_hash is None:
        return False

    return hash_password(password) == stored_hash


def login_gate():
    """
    Renders a login form and blocks access until
    valid credentials are entered. Call this at the
    very top of app.py before any module rendering.

    Returns True if authenticated, False otherwise.
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.markdown("## 🛢️ ResIQ")
    st.markdown("*Reservoir Intelligence Platform*")
    st.divider()
    st.markdown("### Sign In")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Sign In", type="primary"):
        if check_login(username, password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Invalid username or password.")

    return False