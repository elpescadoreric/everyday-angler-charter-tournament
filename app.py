import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

# Initialize SQLite database
conn = sqlite3.connect('tournament.db', check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS uploads (id INTEGER PRIMARY KEY, user TEXT, division TEXT, species TEXT, weight REAL, evidence BLOB, timestamp TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, user TEXT, content TEXT, media BLOB, likes INTEGER, comments TEXT, timestamp TEXT)''')
conn.commit()

# Helper functions
def hash_password(pw):
    return pw  # Replace with real hashing (e.g., bcrypt) in production

def register_user(username, password, role='angler'):
    if not username or not password:
        st.error("Username and password required")
        return False
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, hash_password(password), role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Username already exists")
        return False

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    return c.fetchone()

def save_upload(user, division, species, weight, evidence):
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO uploads (user, division, species, weight, evidence, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
              (user, division, species, weight, evidence.read(), timestamp))
    conn.commit()

def get_leaderboard(division):
    c.execute("SELECT user, species, weight, timestamp FROM uploads WHERE division=? ORDER BY weight DESC LIMIT 10", (division,))
    data = c.fetchall()
    df = pd.DataFrame(data, columns=['User', 'Species', 'Weight (lbs)', 'Date'])
    # Apply sailfish bonus if applicable
    df['Weight (lbs)'] = df.apply(lambda row: row['Weight (lbs)'] + 10 if 'sailfish' in row['Species'].lower() else row['Weight (lbs)'], axis=1)
    return df.sort_values('Weight (lbs)', ascending=False)

def save_post(user, content, media=None):
    timestamp = datetime.now().isoformat()
    media_data = media.read() if media else None
    c.execute("INSERT INTO posts (user, content, media, likes, comments, timestamp) VALUES (?, ?, ?, 0, '', ?)",
              (user, content, media_data, timestamp))
    conn.commit()

def get_social_feed():
    c.execute("SELECT user, content, likes, comments, timestamp FROM posts ORDER BY timestamp DESC LIMIT 20")
    return c.fetchall()

# Streamlit App
st.title("Everyday Angler Charter Tournament App")

# Sidebar for login/register
with st.sidebar:
    st.header("Authentication")
    menu = st.radio("Select", ["Login", "Register"])
    if menu == "Register":
        reg_user = st.text_input("New Username")
        reg_pw = st.text_input("New Password", type="password")
        role = st.selectbox("Role", ["Angler", "Captain"])
        if st.button("Register"):
            if register_user(reg_user, reg_pw, role.lower()):
                st.success("Registered! Now login.")
    else:
        login_user_input = st.text_input("Username")
        login_pw = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(login_user_input, login_pw)
            if user:
                st.session_state['user'] = user[0]
                st.session_state['role'] = user[2]
                st.success(f"Welcome, {user[0]}!")
            else:
                st.error("Invalid credentials")

# Main content – require login
if 'user' not in st.session_state:
    st.warning("Please login or register to access the app.")
else:
    st.subheader(f"Welcome, {st.session_state['user']} ({st.session_state['role'].capitalize()})")

    tab1, tab2, tab3, tab4 = st.tabs(["Upload Evidence", "Leaderboards", "Social Feed", "Admin (if applicable)"])

    with tab1:
        st.header("Upload Catch Evidence")
        division = st.selectbox("Division", ["Pelagic", "Reef"])
        species = st.text_input("Species")
        weight = st.number_input("Weight (lbs)", min_value=0.0)
        evidence = st.file_uploader("Upload Video/Photo Evidence", type=["mp4", "jpg", "png"])
        if st.button("Submit Catch"):
            if evidence:
                save_upload(st.session_state['user'], division, species, weight, evidence)
                st.success("Catch uploaded successfully!")
            else:
                st.error("Evidence file required")

    with tab2:
        st.header("Leaderboards")
        div_select = st.selectbox("View Division", ["Pelagic", "Reef"])
        leaderboard = get_leaderboard(div_select)
        st.dataframe(leaderboard)
        st.subheader("3-Fish Bag Champions")
        st.write("Top bags calculated from aggregated weights – coming soon!")  # Expand with query if needed

    with tab3:
        st.header("Social Feed")
        content = st.text_area("Share an update (e.g., big catch story)")
        media = st.file_uploader("Add Photo/Video", type=["mp4", "jpg", "png"], key="social_upload")
        if st.button("Post"):
            save_post(st.session_state['user'], content, media)
            st.success("Posted!")
        feed = get_social_feed()
        for post in feed:
            st.write(f"**{post[0]}** ({post[4]}): {post[1]}")
            st.write(f"Likes: {post[2]} | Comments: {post[3]}")
            if st.button("Like", key=f"like_{post[4]}"):  # Placeholder – update likes in DB
                st.write("Liked!")

    with tab4:
        if st.session_state['role'] == 'admin':  # Add admin role in users table
            st.header("Admin Dashboard")
            st.write("Approve uploads and manage leaderboards here.")
            # Query and display pending uploads for approval
            c.execute("SELECT * FROM uploads")
            pending = pd.DataFrame(c.fetchall(), columns=['ID', 'User', 'Division', 'Species', 'Weight', 'Evidence', 'Timestamp'])
            st.dataframe(pending)
        else:
            st.warning("Admin access only")

# Logout
if st.sidebar.button("Logout"):
    del st.session_state['user']
    del st.session_state['role']
    st.success("Logged out")
