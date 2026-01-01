import streamlit as st
import pandas as pd
from datetime import datetime

# In-memory storage (resets on redeploy – perfect for testing)
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'uploads' not in st.session_state:
    st.session_state.uploads = []
if 'posts' not in st.session_state:
    st.session_state.posts = []

# Simple functions
def register(username, password, role='angler'):
    if username in st.session_state.users:
        st.error("Username taken")
        return False
    st.session_state.users[username] = {'password': password, 'role': role}
    return True

def login(username, password):
    user = st.session_state.users.get(username)
    if user and user['password'] == password:
        st.session_state.logged_user = username
        st.session_state.role = user['role']
        return True
    return False

def submit_catch(user, division, species, weight):
    st.session_state.uploads.append({
        'user': user, 'division': division, 'species': species.lower(),
        'weight': weight, 'date': datetime.now().strftime("%Y-%m-%d")
    })

def get_leaderboard(division):
    df = pd.DataFrame([u for u in st.session_state.uploads if u['division'] == division])
    if df.empty:
        return pd.DataFrame(columns=['User', 'Species', 'Weight (lbs)', 'Date'])
    # Sailfish bonus
    df['adj_weight'] = df.apply(lambda row: row['weight'] + 10 if 'sailfish' in row['species'] else row['weight'], axis=1)
    df = df.sort_values('adj_weight', ascending=False)[['user', 'species', 'weight', 'date']]
    return df.rename(columns={'user': 'User', 'species': 'Species', 'weight': 'Weight (lbs)', 'date': 'Date'})

def add_post(user, content):
    st.session_state.posts.append({'user': user, 'content': content, 'date': datetime.now().strftime("%Y-%m-%d")})

# App UI
st.title("Everyday Angler Charter Tournament")

if 'logged_user' not in st.session_state:
    tab = st.tabs(["Login/Register"])[0]
    with st.form("auth"):
        action = st.radio("Action", ["Login", "Register"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if action == "Register":
            role = st.selectbox("Role", ["Angler", "Captain"])
        submitted = st.form_submit_button("Submit")
        if submitted:
            if action == "Register":
                if register(username, password, role.lower()):
                    st.success("Registered! Log in now.")
            else:
                if login(username, password):
                    st.success("Logged in!")
                    st.rerun()

else:
    st.success(f"Logged in as {st.session_state.logged_user} ({st.session_state.role})")
    if st.button("Logout"):
        del st.session_state.logged_user
        del st.session_state.role
        st.rerun()

    tabs = st.tabs(["Submit Catch", "Leaderboards", "Social Feed"])

    with tabs[0]:
        st.header("Submit Catch")
        division = st.selectbox("Division", ["Pelagic", "Reef"])
        species = st.text_input("Species")
        weight = st.number_input("Weight (lbs)", min_value=0.0)
        if st.button("Submit Catch"):
            submit_catch(st.session_state.logged_user, division, species, weight)
            st.success("Submitted!")

    with tabs[1]:
        st.header("Leaderboards")
        div = st.selectbox("Division", ["Pelagic", "Reef"])
        st.dataframe(get_leaderboard(div))

    with tabs[2]:
        st.header("Social Feed")
        content = st.text_area("Post update")
        if st.button("Post"):
            add_post(st.session_state.logged_user, content)
            st.success("Posted!")
        for post in reversed(st.session_state.posts[-20:]):
            st.write(f"**{post['user']}** ({post['date']}): {post['content']}")

st.caption("Prototype App – Data resets on redeploy")
