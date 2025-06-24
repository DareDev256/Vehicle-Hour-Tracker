import streamlit as st

# This is the minimal working app for Streamlit Cloud
st.title("🚗 Vehicle Hour Tracker")
st.write("Hello! This is a test to see if the basic deployment works.")

# Simple form
with st.form("test_form"):
    name = st.text_input("Enter your name:")
    submitted = st.form_submit_button("Submit")
    
    if submitted and name:
        st.success(f"Hello {name}! The app is working!")