import streamlit as st
import extra_streamlit_components as stx
from database import register_user, login_user

# Initialize Cookie Manager
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# Function to Set Cookie
def set_cookie(key, value):
    cookie_manager.set(key, value)

# Function to Get Cookie
def get_cookie(key):
    return cookie_manager.get(key)

def registration_page():
    st.subheader("Create an Account")
    username = st.text_input("Enter Username")
    email = st.text_input("Enter Email")
    password = st.text_input("Enter Password", type="password")

    if st.button("Register"):
        if username and email and password:
            msg = register_user(username, email, password)
            st.success(msg)
        else:
            st.error("All fields are required!")

def login_page():
    st.warning("Sign up If you are a new user!")
    st.subheader("Login to Your Account")
    email = st.text_input("Enter Email")
    password = st.text_input("Enter Password", type="password")

    if st.button("login"):
        user = login_user(email, password)
        if user:
            st.session_state["user_id"] = user["id"]
            st.session_state["username"] = user["username"]
            st.session_state["logged_in"] = True

            # Store login session in cookies
            set_cookie("logged_in", "True")
            set_cookie("user_id", str(user["id"]))  # Convert to string for cookies
            set_cookie("username", user["username"])


            st.success(f"Welcome {user['username']}!")
            st.rerun()
        else:
            st.error("Invalid email or password!")
