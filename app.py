import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Use in-memory storage for prototype (SQLite can be tricky on Streamlit Cloud)
if 'users' not in st.session_state:
    st.session_state.users = {}  # {username: {'password': pw, 'role': role}}
if 'uploads' not in st.session_state:
    st.session_state.uploads = []  # list of dicts
if 'posts' not in st.session_state:
    st.session_state.posts = []  # list of dicts

# Helper functions (in-memory version)
def register_user(username, password, role='angler'):
    if username in st.session_state.users:
        st.error("Username already exists")
        return False
    st.session_state.users[username] = {'password': password, 'role': role}  # No hashing for prototype
    return True

def login_user(username, password):
    user = st.session_state.users.get(username)
    if user and user['password'] == password:
        return (username, user['role'])
    return None

def save_upload(user, division, species, weight, evidence_name):
    timestamp = datetime.now().isoformat()
    st.session_state.uploads.append({
        'user': user, 'division': division, 'species': species,
        'weight': weight, 'evidence': evidence_name, 'timestamp': timestamp
    })

def get_leaderboard(division):
    df = pd.DataFrame([u for u in st.session_state.uploads if u['division'] == division])
    if df.empty:
        return pd.DataFrame(columns=['User', 'Species', 'Weight (lbs)', 'Date'])
    # Apply sailfish bonus
    df['Weight (lbs)'] = df.apply(lambda row: row['weight'] + 10 if 'sailfish' in row['species'].lower() else row['weight'], axis=1)
    df = df.sort_values('Weight (lbs)', ascending=False).head(10)
    return df[['user', 'species', 'Weight (lbs)', 'timestamp']].rename(columns={'user': 'User', 'species': 'Species', 'timestamp': 'Date'})

def save_post(user, content, media_name=None):
    timestamp = datetime.now().isoformat()
    st.session_state.posts.append({
        'user': user, 'content': content, 'media': media_name, 'likes': 0, 'timestamp': timestamp
    })

def get_social_feed():
    return st.session_state.posts[-20:]

# Streamlit App
st.title("Everyday Angler Charter Tournament App")

# Sidebar login
with st.sidebar:
    st.header("Login / Register")
    menu = st.radio("Action", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if menu == "Register":
        role = st.selectbox("Role", ["Angler", "Captain"])
        if st.button("Register"):
            if register_user(username, password, role.lower()):
                st.success("Registered! Now log in.")
    else:
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_user = user[0]
                st.session_state.role = user[1]
                st.success(f"Welcome, {user[0]}!")
            else:
                st.error("Invalid credentials")

# Main content
if 'logged_user' not in st.session_state:
    st.warning("Please log in or register.")
else:
    st.success(f"Logged in as {st.session_state.logged_user} ({st.session_state.role.capitalize()})")

    tab1, tab2, tab3 = st.tabs(["Upload Catch", "Leaderboards", "Social Feed"])

    with tab1:
        st.header("Submit Catch")
        division = st.selectbox("Division", ["Pelagic", "Reef"])
        species = st.text_input("Species (e.g., Dolphin, Wahoo, Tuna)")
        weight = st.number_input("Weight (lbs)", min_value=0.0, step=0.1)
        evidence = st.file_uploader("Video/Photo Evidence", type=["mp4", "jpg", "png", "mov"])
        if st.button("Submit"):
            if evidence:
                save_upload(st.session_state.logged_user, division, species, weight, evidence.name)
                st.success("Catch submitted!")
            else:
                st.error("Please upload evidence")

    with tab2:
        st.header("Leaderboards")
        div = st.selectbox("Division", ["Pelagic", "Reef"])
        lb = get_leaderboard(div)
        st.dataframe(lb)

    with tab3:
        st.header("Social Feed")
        content = st.text_area("Share your fishing story")
        media = st.file_uploader("Add photo/video", key="social")
        if st.button("Post"):
            save_post(st.session_state.logged_user, content, media.name if media else None)
            st.success("Posted!")
        for post in reversed(get_social_feed()):
            st.write(f"**{post['user']}** – {post['timestamp'][:10]}")
            st.write(post['content'])
            if post['media']:
                st.write(f"Attached: {post['media']}")
            st.write(f"Likes: {post['likes']}")
            st.divider()

    if st.button("Logout"):
        del st.session_state.logged_user
        del st.session_state.role
        st.rerun()
