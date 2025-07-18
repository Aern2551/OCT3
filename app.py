import streamlit as st

# CSS สไตล์จากโค้ดที่คุณให้มา (ตัดมาเฉพาะส่วนที่จำเป็น)
custom_css = """
<style>
.upload-area {
    border: 2px dashed #d1d5db;
    transition: all 0.3s ease;
}

.upload-area:hover {
    border-color: #3EB489;
    background-color: #f0fdf4;
}

.login-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 12px;
    max-width: 400px;
    margin: auto;
    color: white;
}

input[type="text"], input[type="password"] {
    width: 100%;
    padding: 12px 15px;
    margin: 8px 0 16px 0;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-sizing: border-box;
    outline: none;
    transition: border-color 0.3s ease;
}

input[type="text"]:focus, input[type="password"]:focus {
    border-color: #3EB489;
    box-shadow: 0 0 5px #3EB489;
}

button {
    background-color: #3EB489;
    color: white;
    padding: 12px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
    width: 100%;
    transition: background-color 0.3s ease;
}

button:hover {
    background-color: #2e8b6f;
}
</style>
"""

def login_form():
    st.markdown(custom_css, unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In")
        st.markdown("</div>", unsafe_allow_html=True)
    return username, password, submitted

def main():
    st.title("RetinaView AI - Login")

    username, password, submitted = login_form()

    # ตัวอย่างเช็ค username/password แบบง่ายๆ
    if submitted:
        if username == "doctor" and password == "password123":
            st.success(f"Welcome, {username}!")
            # ทำอย่างอื่นเช่น เปลี่ยนหน้า หรือ session state ฯลฯ
        else:
            st.error("Invalid username or password")

if __name__ == "__main__":
    main()
