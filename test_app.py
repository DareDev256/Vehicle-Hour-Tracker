import streamlit as st

def main():
    st.title("🚗 Test App")
    st.write("If you can see this, the basic Streamlit setup works!")
    
    # Test basic functionality
    name = st.text_input("Enter your name:")
    if name:
        st.write(f"Hello, {name}!")

if __name__ == "__main__":
    main()