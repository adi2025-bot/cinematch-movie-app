import streamlit as st
import pickle
import gzip
import pandas as pd
import hashlib
import os
import requests
import ast
import time
import urllib.parse
import plotly.express as px
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import textwrap
import textwrap

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="CineMatch Ultimate", 
    page_icon="🍿",
    initial_sidebar_state="expanded"
)

# YOUR API KEY
API_KEY = "e9324b946a1cfdd8f612f18690be72d7" 

# --- INIT SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'view_mode' not in st.session_state: st.session_state.view_mode = 'grid'
if 'detail_movie' not in st.session_state: st.session_state.detail_movie = None
if 'selected_movie' not in st.session_state: st.session_state.selected_movie = None
if 'selected_director' not in st.session_state: st.session_state.selected_director = None
if 'selected_actor' not in st.session_state: st.session_state.selected_actor = None
if 'selected_genre' not in st.session_state: st.session_state.selected_genre = None
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ''
if 'role' not in st.session_state: st.session_state.role = 'user'
if 'search_type' not in st.session_state: st.session_state.search_type = 'movie'
if 'search_query' not in st.session_state: st.session_state.search_query = None

# ==========================================
# 2. VISUAL STYLE
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    
    .stApp { background: radial-gradient(circle at top left, #0f0c29, #302b63, #24243e); color: #ffffff; }
    
    #MainMenu, footer {visibility: hidden;} 
    div[data-testid="stVerticalBlock"] > div:first-child { padding-top: 0; }
    
    /* NAVBAR */
    .nav-header {
        background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(15px);
        padding: 20px 40px; border-bottom: 1px solid rgba(255,255,255,0.1);
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;
        border-radius: 0 0 20px 20px;
    }
    .logo { font-size: 32px; font-weight: 800; color: #e50914; letter-spacing: 2px; text-transform: uppercase; text-shadow: 0 0 10px rgba(229,9,20,0.6); }
    .user-badge { font-weight: 600; color: #ddd; }
    
    /* MOVIE CARD */
    .movie-card {
        text-decoration: none; color: white; display: block;
        background: #161b22; border-radius: 15px; overflow: hidden;
        border: 1px solid rgba(255,255,255,0.05); transition: 0.3s;
        height: 100%; cursor: pointer;
        margin-bottom: 25px; /* Vertical Gap */
    }
    .movie-card:hover { transform: scale(1.04); border-color: #e50914; z-index: 10; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .movie-card img { width: 100%; aspect-ratio: 2/3; object-fit: cover; display: block;}
    .card-content { padding: 12px; }
    .card-title { font-size: 1rem; font-weight: 700; margin: 0 0 5px 0; line-height: 1.2; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .card-meta { font-size: 0.85rem; color: #aaa; }
    
    /* HERO SECTION */
    .hero-container {
        position: relative; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.8); margin-bottom: 30px;
        background-size: cover; background-position: center; min-height: 500px;
    }
    .hero-overlay {
        background: linear-gradient(to right, #000000 20%, rgba(0,0,0,0.85) 50%, rgba(0,0,0,0.1));
        padding: 50px; display: flex; gap: 40px; align-items: center; height: 100%; min-height: 500px;
    }
    .hero-poster { width: 300px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.8); border: 2px solid rgba(255,255,255,0.1); }
    .hero-content { color: white; flex: 1; max-width: 800px;}
    .hero-title { font-size: 3.8rem; font-weight: 800; line-height: 1.1; margin-bottom: 10px; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }
    .tagline { font-size: 1.2rem; font-style: italic; color: #e50914; margin-bottom: 20px; font-weight: 500;}
    
    /* STATS ROW */
    .stats-row { display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap;}
    .stat-pill { background: rgba(255,255,255,0.15); backdrop-filter: blur(5px); padding: 6px 16px; border-radius: 50px; font-weight: 600; font-size: 0.9rem; border: 1px solid rgba(255,255,255,0.2); }
    
    /* CAST CIRCLES */
    .cast-container { text-align: center; margin-bottom: 15px; }
    .cast-img { border-radius: 15px; width: 100%; object-fit: cover; aspect-ratio: 1/1; margin-bottom: 8px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
    .cast-name { font-size: 0.9rem; font-weight: 600; line-height: 1.2; }
    
    /* SIDEBAR INFO */
    .info-box { background: rgba(255,255,255,0.03); padding: 20px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 20px; }
    .info-label { color: #aaa; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .info-val { font-size: 1.1rem; font-weight: 600; margin-bottom: 15px; color: #fff; }
    
    /* STREAMING */
    .stream-badge { display: inline-block; padding: 6px 12px; background: #fff; color: #000; border-radius: 6px; margin: 4px; font-weight: 700; font-size: 0.8rem; }
    
    /* REVIEWS */
    .review-card { background: #1f2633; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #e50914; }
    .sentiment-pos { color: #46d369; font-weight: bold; font-size: 0.8rem; float: right; }
    
    /* BUTTONS */
    .stButton>button { 
        background: linear-gradient(135deg, #e50914, #ff5f6d); color: white; border-radius: 8px; border: none; font-weight: 700; padding: 10px 0; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(229, 9, 20, 0.4); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATABASE & AUTH
# ==========================================
def make_hashes(p): return hashlib.sha256(str.encode(p)).hexdigest()

def create_dbs():
    if not os.path.exists('users.csv'): pd.DataFrame(columns=['username','password','role']).to_csv('users.csv',index=False)
    if not os.path.exists('watchlist.csv'): pd.DataFrame(columns=['username','movie','date']).to_csv('watchlist.csv',index=False)
    if not os.path.exists('feedback.csv'): pd.DataFrame(columns=['username','movie','feedback','date']).to_csv('feedback.csv',index=False)
    if not os.path.exists('reviews.csv'): 
        pd.DataFrame(columns=['username','movie','rating','review','sentiment','date']).to_csv('reviews.csv',index=False)
    else:
        df = pd.read_csv('reviews.csv')
        if 'sentiment' not in df.columns:
            df['sentiment'] = 'Neutral'; df.to_csv('reviews.csv', index=False)

def add_user(u,p):
    create_dbs(); df=pd.read_csv('users.csv')
    if u in df['username'].values: return False
    new=pd.DataFrame({'username':[u],'password':[make_hashes(p)],'role':['user']}); df=pd.concat([df,new],ignore_index=True); df.to_csv('users.csv',index=False); return True

def login_user(u,p):
    create_dbs(); df=pd.read_csv('users.csv'); h=make_hashes(p)
    res=df[(df['username']==u)&(df['password']==h)]
    if not res.empty: return True, res.iloc[0]['role']
    return False, None

def add_to_watchlist(u,m):
    create_dbs(); df=pd.read_csv('watchlist.csv')
    if not ((df['username']==u)&(df['movie']==m)).any():
        new=pd.DataFrame({'username':[u],'movie':[m],'date':[str(datetime.now().date())]}); df=pd.concat([df,new],ignore_index=True); df.to_csv('watchlist.csv',index=False); return True
    return False

def save_feedback(u,m,f):
    create_dbs(); df=pd.read_csv('feedback.csv')
    df = df[~((df['username']==u) & (df['movie']==m))] 
    new=pd.DataFrame({'username':[u],'movie':[m],'feedback':[f],'date':[str(datetime.now().date())]}); df=pd.concat([df,new],ignore_index=True); df.to_csv('feedback.csv',index=False)

def analyze_sentiment(text):
    text = text.lower()
    pos = ['good', 'great', 'awesome', 'excellent', 'love', 'amazing', 'best', 'fantastic']
    neg = ['bad', 'worst', 'terrible', 'boring', 'awful', 'hate', 'poor', 'stupid']
    score = sum([1 for w in pos if w in text]) - sum([1 for w in neg if w in text])
    return "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"

def add_review(u, m, r, text):
    create_dbs(); sentiment = analyze_sentiment(text); df = pd.read_csv('reviews.csv')
    new = pd.DataFrame({'username':[u], 'movie':[m], 'rating':[r], 'review':[text], 'sentiment':[sentiment], 'date':[str(datetime.now().date())]})
    df = pd.concat([df, new], ignore_index=True); df.to_csv('reviews.csv', index=False)

def get_reviews(m): create_dbs(); df = pd.read_csv('reviews.csv'); return df[df['movie'] == m]
def get_watchlist(u): create_dbs(); df=pd.read_csv('watchlist.csv'); return df[df['username']==u]
def get_liked_movies(u): create_dbs(); df=pd.read_csv('feedback.csv'); return df[(df['username']==u) & (df['feedback']=='Like')]
def get_all_users(): return pd.read_csv('users.csv')

# ==========================================
# 4. DATA ENGINE (FIXED & ROBUST)
# ==========================================
# Robust Session setup with Retry strategy
session = requests.Session()
retry_strategy = Retry(
    total=3, 
    backoff_factor=1, 
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

@st.cache_data(ttl=3600)
def fetch_poster_only(movie_id, title="Movie"):
    clean_title = urllib.parse.quote(str(title))
    placeholder = f"https://placehold.co/500x750/1f1f1f/FFFFFF?text={clean_title}"
    try:
        mid = int(float(movie_id))
        url = f"https://api.themoviedb.org/3/movie/{mid}?api_key={API_KEY}&language=en-US"
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('poster_path'):
                return "https://image.tmdb.org/t/p/w500" + data['poster_path']
        return placeholder
    except Exception:
        return placeholder

@st.cache_data(ttl=3600)
def fetch_full_details(movie_id, title="Movie"):
    poster = fetch_poster_only(movie_id, title)
    clean_title = urllib.parse.quote(str(title))
    backdrop = f"https://placehold.co/1200x600/1f1f1f/FFFFFF?text={clean_title}"
    trailer = None; cast_rich = []; director = "Unknown"; providers = []
    
    try:
        mid = int(float(movie_id))
        url = f"https://api.themoviedb.org/3/movie/{mid}?api_key={API_KEY}&append_to_response=credits,videos,watch/providers"
        response = session.get(url, timeout=5)
        
        if response.status_code == 200:
            main = response.json()
            if main.get('backdrop_path'): backdrop = "https://image.tmdb.org/t/p/original" + main['backdrop_path']
            
            if 'credits' in main:
                if 'cast' in main['credits']:
                    for c in main['credits']['cast'][:6]:
                        pic = "https://image.tmdb.org/t/p/w200" + c['profile_path'] if c.get('profile_path') else f"https://via.placeholder.com/200?text={urllib.parse.quote(c['name'])}"
                        cast_rich.append({'name': c['name'], 'photo': pic})
                if 'crew' in main['credits']:
                    director = next((x['name'] for x in main['credits']['crew'] if x['job'] == 'Director'), "Unknown")
            
            if 'videos' in main:
                for t_type in ['Trailer', 'Teaser', 'Clip']:
                    found = next((v['key'] for v in main['videos'].get('results', []) if v['site']=='YouTube' and v['type']==t_type), None)
                    if found: trailer = found; break
            
            if 'watch/providers' in main and 'results' in main['watch/providers']:
                res = main['watch/providers']['results']
                region = 'IN' if 'IN' in res else 'US'
                if region in res and 'flatrate' in res[region]:
                    providers = [p['provider_name'] for p in res[region]['flatrate']]
    except: pass
    
    return {'poster': poster, 'backdrop': backdrop, 'trailer': trailer, 'cast_rich': cast_rich, 'director': director, 'providers': providers}

@st.cache_resource
def load_data():
    try:
        # Load optimized files
        if os.path.exists('movie_list_optimized.pkl'):
            movies_dict = pickle.load(open('movie_list_optimized.pkl','rb'))
        else:
            movies_dict = pickle.load(open('movie_list.pkl','rb'))
            
        if os.path.exists('similarity_optimized.pkl'):
            similarity = pickle.load(open('similarity_optimized.pkl','rb'))
        elif os.path.exists('similarity.pkl.gz'):
            with gzip.open('similarity.pkl.gz', 'rb') as f:
                similarity = pickle.load(f)
        else:
            similarity = pickle.load(open('similarity.pkl','rb'))

        movies = pd.DataFrame(movies_dict)
        movies['year_int'] = pd.to_datetime(movies['release_date'], errors='coerce').dt.year.fillna(0).astype(int)
        movies['vote_average'] = pd.to_numeric(movies['vote_average'], errors='coerce').fillna(0)
        
        if 'movie_id' not in movies.columns and 'id' in movies.columns:
            movies.rename(columns={'id': 'movie_id'}, inplace=True)
            
        return movies, similarity
    except Exception as e: 
        st.error(f"Error loading data files: {e}"); return None, None

movies, similarity = load_data()

def process_movie_for_ui(row):
    details = fetch_full_details(row.movie_id, row.title)
    genres = "N/A"
    if 'genres_list' in row:
        val = row.genres_list
        if isinstance(val, list): genres = ", ".join(val)
        elif isinstance(val, str): genres = val
    
    final_cast = details['cast_rich']
    if not final_cast and 'top_cast' in row:
        local_cast = row.top_cast if isinstance(row.top_cast, list) else []
        for actor_name in local_cast[:6]: 
            final_cast.append({'name': actor_name, 'photo': "https://via.placeholder.com/200?text=" + actor_name.split()[0]})
            
    def fmt_curr(val): return "${:,.0f}".format(val) if val and val > 0 else "N/A"
    def fmt_run(val): return f"{int(val//60)}h {int(val%60)}m" if val and val > 0 else "N/A"
    
    rating_val = f"{int(row.vote_average * 10)}%" if row.vote_average > 0 else "NR"
    year_val = str(row.release_date)[:4] if row.release_date and str(row.release_date) != "nan" else "N/A"
    
    return {
        'id': row.movie_id, 'title': row.title,
        'year': year_val, 'rating_perc': rating_val,
        'runtime': fmt_run(row.runtime) if 'runtime' in row else "N/A",
        'genres': genres, 'tagline': row.tagline if hasattr(row, 'tagline') and row.tagline else "",
        'overview': row.overview if row.overview else "No summary available.",
        'cast_rich': final_cast, 'director': details['director'],
        'poster': details['poster'], 'backdrop': details['backdrop'], 'trailer': details['trailer'],
        'providers': details['providers'], 'budget': fmt_curr(row.budget) if 'budget' in row else "N/A",
        'revenue': fmt_curr(row.revenue) if 'revenue' in row else "N/A",
        'production': row.production_str if 'production_str' in row else "N/A",
        'status': row.status if 'status' in row else "Released"
    }

def process_grid_item(row):
    poster = fetch_poster_only(row.movie_id, row.title)
    year_val = str(row.release_date)[:4] if row.release_date and str(row.release_date) != "nan" else "N/A"
    rating_val = f"⭐ {int(row.vote_average * 10)}%" if row.vote_average > 0 else "NR"
    return {'id': row.movie_id, 'title': row.title, 'poster': poster, 'year': year_val, 'rating': rating_val}

def recommend(movie_title):
    if isinstance(similarity, dict):
        try:
            indices = similarity.get(movie_title, [])
            with ThreadPoolExecutor(max_workers=3) as executor:
                results = list(executor.map(process_grid_item, [movies.iloc[i] for i in indices]))
            return results
        except: return []
    return recommend_legacy(movie_title)

def recommend_legacy(movie_title):
    try:
        idx = movies[movies['title'] == movie_title].index[0]
        distances = similarity[idx]
        m_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(process_grid_item, [movies.iloc[i[0]] for i in m_list]))
        return results
    except: return []

def get_top_movies():
    C=movies['vote_average'].mean(); m=movies['vote_count'].quantile(0.9)
    q=movies.copy().loc[movies['vote_count']>=m]
    q['score']=q.apply(lambda x: (x['vote_count']/(x['vote_count']+m)*x['vote_average'])+(m/(m+x['vote_count'])*C), axis=1)
    return q.sort_values('score',ascending=False).head(20)

# HELPER: Render Grid
def display_movies_grid(movies_to_show):
    if not movies_to_show:
        st.info("No movies found.")
        return
    for i in range(0, len(movies_to_show), 5):
        # Added gap="medium" for horizontal spacing
        cols = st.columns(5, gap="medium")
        batch = movies_to_show[i:i+5]
        for idx, data in enumerate(batch):
            with cols[idx]:
                link_url = f"?id={data['id']}&user={st.session_state.username}"
                st.markdown(textwrap.dedent(f"""
                <a href="{link_url}" target="_self" style="text-decoration:none;">
                    <div class="movie-card">
                        <img src="{data['poster']}">
                        <div class="card-content">
                            <div class="card-title">{data['title']}</div>
                            <div class="card-meta">{data['rating']}</div>
                        </div>
                    </div>
                </a>
                """), unsafe_allow_html=True)

# Navigation
def set_detail(movie_id): 
    row = movies[movies['movie_id'] == movie_id].iloc[0]
    data = process_movie_for_ui(row)
    st.session_state.view_mode='detail'; st.session_state.detail_movie=data
    st.query_params["id"] = movie_id 

def go_grid(): 
    st.session_state.view_mode='grid'; 
    st.session_state.detail_movie=None
    if "id" in st.query_params: del st.query_params["id"]

def set_page(p): st.session_state.page=p; st.session_state.view_mode='grid'

def search_movie(movie_name):
    st.session_state.page='search'
    st.session_state.view_mode='grid'
    st.session_state.search_type='movie'
    st.session_state.search_query=movie_name

def search_director_movies(director_name):
    st.session_state.page='search'
    st.session_state.view_mode='grid'
    st.session_state.search_type='director'
    st.session_state.search_query=director_name

def search_actor_movies(actor_name):
    st.session_state.page='search'
    st.session_state.view_mode='grid'
    st.session_state.search_type='actor'
    st.session_state.search_query=actor_name

# ==========================================
# 5. MAIN APPLICATION
# ==========================================

# --- CHECK URL STATE FIRST ---
if 'id' in st.query_params and not st.session_state.detail_movie:
    try: mid = int(st.query_params["id"]); set_detail(mid)
    except: pass

if not st.session_state.logged_in:
    if "user" in st.query_params: st.session_state.logged_in=True; st.session_state.username=st.query_params["user"]; st.rerun()
    
    col1,col2,col3=st.columns([1,2,1])
    with col2:
        st.markdown("<br><br><h1 style='text-align:center; color:#e50914; font-size:50px;'>CineMatch</h1>", unsafe_allow_html=True)
        tab1,tab2=st.tabs(["Login","Register"])
        
        with tab1:
            u=st.text_input("Username"); p=st.text_input("Password",type='password')
            if st.button("Enter", use_container_width=True):
                v,r=login_user(u,p)
                if v: st.session_state.logged_in=True; st.session_state.username=u; st.session_state.role=r; st.query_params["user"]=u; st.rerun()
                else: st.error("Invalid")
        
        with tab2:
            nu=st.text_input("New User"); np=st.text_input("New Pass",type='password')
            if st.button("Create", use_container_width=True): 
                if add_user(nu,np): st.success("Success!"); 
                else: st.error("Taken")

else:
    # --- LOGGED IN HEADER ---
    st.markdown(textwrap.dedent(f"""<div class="nav-header"><div class="logo">CineMatch</div><div class="user-badge">👤 {st.session_state.username}</div></div>"""), unsafe_allow_html=True)
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### 🔍 Quick Search")
        search_q = st.selectbox("Find Movie", movies['title'].values, index=None, placeholder="Type movie name...", label_visibility="collapsed")
        
        if st.button("Go Search", type="primary", use_container_width=True):
            if search_q: search_movie(search_q); st.rerun()
        
        st.markdown("---")
        st.button("🏠 Home", use_container_width=True, on_click=set_page, args=('home',))
        st.button("❤️ Watchlist", use_container_width=True, on_click=set_page, args=('watchlist',))
        st.button("👍 Liked", use_container_width=True, on_click=set_page, args=('liked',))
        
        if st.session_state.username == 'admin': 
            if st.button("📊 Admin Dashboard", use_container_width=True): st.session_state.page='admin'; st.session_state.view_mode='grid'; st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("☰ Filters"):
            all_genres = set()
            for sublist in movies['genres_list']:
                if isinstance(sublist, list):
                    for g in sublist: all_genres.add(g)
            
            sel_g = st.selectbox("By Genre", ["All"]+sorted(list(all_genres)))
            
            if st.button("Filter Genre"): 
                st.session_state.page='genre'; st.session_state.selected_genre=sel_g; st.session_state.view_mode='grid'; st.rerun()
        
        st.markdown("---")
        if st.button("Logout"): st.session_state.logged_in=False; st.query_params.clear(); st.rerun()

    # --- MAIN CONTENT AREA ---
    
    # 1. MOVIE DETAIL VIEW (NEW LAYOUT + DYNAMIC BACK BUTTON)
    if st.session_state.view_mode == 'detail' and st.session_state.detail_movie:
        m = st.session_state.detail_movie
        
        # --- ✅ DYNAMIC BACK BUTTON LOGIC ---
        back_label = "← Back"
        if st.session_state.page == 'home': back_label = "← Back to Home"
        elif st.session_state.page == 'genre': back_label = f"← Back to {st.session_state.selected_genre}"
        elif st.session_state.page == 'search': back_label = "← Back to Search Results"
        elif st.session_state.page == 'watchlist': back_label = "← Back to Watchlist"
        elif st.session_state.page == 'liked': back_label = "← Back to Liked Movies"

        if st.button(back_label, type="secondary"): 
            go_grid() 
            st.rerun()
        
        # 2. Hero Section
        st.markdown(textwrap.dedent(f"""
        <div class="hero-container" style="background-image: url('{m['backdrop']}');">
            <div class="hero-overlay">
                <img src="{m['poster']}" class="hero-poster">
                <div class="hero-content">
                    <h1 class="hero-title">{m['title']}</h1>
                    <div class="tagline">{m['tagline']}</div>
                    <div class="stats-row">
                        <span class="stat-pill">⭐ {m['rating_perc']} Match</span>
                        <span class="stat-pill">📅 {m['year']}</span>
                        <span class="stat-pill">⏱ {m['runtime']}</span>
                        <span class="stat-pill">🎭 {m['genres']}</span>
                    </div>
                    <p style="font-size:1.2rem; line-height:1.6; opacity:0.9; margin-top:20px;">{m['overview']}</p>
                </div>
            </div>
        </div>
        """), unsafe_allow_html=True)
        
        # 3. Main Split (Left: Content, Right: Info)
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("### 🎭 Top Cast")
            if m['cast_rich']:
                cols = st.columns(6)
                for i, actor in enumerate(m['cast_rich'][:6]):
                    with cols[i]:
                        st.markdown(textwrap.dedent(f"""
                        <div class="cast-container">
                            <img src="{actor['photo']}" class="cast-img">
                        </div>
                        """), unsafe_allow_html=True)
                        if st.button(actor['name'].split()[0], key=f"act_{i}", use_container_width=True): 
                             search_actor_movies(actor['name']); st.rerun()
            else: st.info("No cast info available.")
            
            st.markdown("### 🎬 Trailer & Clips")
            if m['trailer']:
                st.video(f"https://www.youtube.com/watch?v={m['trailer']}")
            else:
                st.link_button("🔎 Search Trailer on YouTube", f"https://www.youtube.com/results?search_query={m['title']}+trailer", use_container_width=True)
            
            st.markdown("### 📰 User Reviews")
            revs = get_reviews(m['title'])
            if not revs.empty:
                for _, r in revs.iterrows():
                    st.markdown(textwrap.dedent(f"""<div class="review-card"><div><strong>{r['username']}</strong> <span class="sentiment-pos">{r['sentiment']}</span></div><div style="margin-top:5px; color:#ddd;">"{r['review']}"</div></div>"""), unsafe_allow_html=True)
            else:
                st.caption("No reviews yet. Be the first!")

        with col_right:
            # Action Buttons
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("❤️ Watchlist", use_container_width=True): add_to_watchlist(st.session_state.username, m['title']); st.toast("Added to Watchlist")
            with c_btn2:
                if st.button("👍 Like", use_container_width=True): save_feedback(st.session_state.username, m['title'], "Like"); st.toast("Liked Movie")
            
            # Info Box
            st.markdown("""<div class="info-box">""", unsafe_allow_html=True)
            st.markdown(f"<div class='info-label'>Director</div><div class='info-val'>{m['director']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='info-label'>Budget</div><div class='info-val'>{m['budget']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='info-label'>Revenue</div><div class='info-val'>{m['revenue']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='info-label'>Status</div><div class='info-val'>{m['status']}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Streaming
            st.markdown("### 📺 Where to Watch")
            if m['providers']:
                html = '<div style="margin-bottom:20px;">'
                for p in m['providers']: html += f'<span class="stream-badge">{p}</span>'
                html += '</div>'; st.markdown(html, unsafe_allow_html=True)
            else: 
                st.info("Not currently streaming in your region.")

            # Review Form
            st.markdown("### ✍️ Rate this Movie")
            with st.form("rev_form"):
                rev_txt = st.text_area("Write a review...", height=100)
                rev_score = st.slider("Rating", 1, 10, 8)
                if st.form_submit_button("Submit Review", use_container_width=True): 
                    add_review(st.session_state.username, m['title'], rev_score, rev_txt)
                    st.success("Review Posted!")
                    st.rerun()

    # 2. ADMIN VIEW
    elif st.session_state.page == 'admin':
        st.title("📊 Admin Dashboard")
        try:
            df_likes = pd.read_csv('feedback.csv')
            df_watch = pd.read_csv('watchlist.csv')
            df_reviews = pd.read_csv('reviews.csv')
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Likes", len(df_likes))
            c2.metric("Watchlist Adds", len(df_watch))
            c3.metric("Reviews Posted", len(df_reviews))
            st.markdown("---")
            
            if not df_likes.empty:
                st.subheader("❤️ Most Liked Movies")
                top_likes = df_likes['movie'].value_counts().reset_index()
                top_likes.columns = ['Movie', 'Count']
                fig = px.bar(top_likes.head(10), x='Movie', y='Count', color='Count', title="Top 10 Liked Movies")
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("🍕 Genre Popularity")
                liked_titles = df_likes['movie'].unique()
                liked_movies_info = movies[movies['title'].isin(liked_titles)]
                
                all_genres = []
                for g_list in liked_movies_info['genres_list']:
                    if isinstance(g_list, list): all_genres.extend(g_list)
                    elif isinstance(g_list, str): all_genres.append(g_list)
                
                if all_genres:
                    genre_counts = pd.Series(all_genres).value_counts().reset_index()
                    genre_counts.columns = ['Genre', 'Count']
                    fig2 = px.pie(genre_counts, values='Count', names='Genre', title="User Taste Distribution")
                    st.plotly_chart(fig2, use_container_width=True)
            else: st.info("No data for genres.")
            
            st.markdown("---")
            st.subheader("Recent User Activity")
            st.write("Recent Reviews:")
            st.dataframe(df_reviews.tail(5))
            
        except Exception as e:
            st.error(f"Could not load analytics. Make sure CSV files exist. Error: {e}")

    # 3. GRID VIEWS (HOME, SEARCH, WATCHLIST, ETC)
    else:
        movies_to_show = []
        title_text = ""
        
        if st.session_state.page == 'home':
            title_text = "🔥 Trending Now"
            top_df = get_top_movies()
            with ThreadPoolExecutor(max_workers=3) as executor:
                movies_to_show = list(executor.map(process_grid_item, [row for _, row in top_df.iterrows()]))
            st.markdown(f"### {title_text}")
            display_movies_grid(movies_to_show)
        
        elif st.session_state.page == 'genre':
            g = st.session_state.selected_genre
            title_text = f"📂 Genre: {g}"
            if g == "All": sub_df = movies.head(20)
            else: sub_df = movies[movies['genres_list'].apply(lambda x: g in x)].head(20)
            with ThreadPoolExecutor(max_workers=3) as executor:
                movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
            st.markdown(f"### {title_text}")
            display_movies_grid(movies_to_show)

        elif st.session_state.page == 'search':
            q_type = st.session_state.search_type
            query = st.session_state.search_query
            
            if q_type == 'movie':
                exact_match = movies[movies['title'].str.lower() == query.lower()]
                
                if not exact_match.empty:
                    exact_movie = exact_match.iloc[0]
                    st.markdown(f"### Result for: {exact_movie['title']}")
                    st.markdown("---")
                    
                    exact_grid_item = process_grid_item(exact_movie)
                    
                    col_ex_1, col_ex_2, col_ex_3, col_ex_4, col_ex_5 = st.columns(5)
                    with col_ex_1:
                        link_url = f"?id={exact_grid_item['id']}&user={st.session_state.username}"
                        st.markdown(textwrap.dedent(f"""
                        <a href="{link_url}" target="_self" style="text-decoration:none;">
                            <div class="movie-card">
                                <img src="{exact_grid_item['poster']}">
                                <div class="card-content">
                                    <div class="card-title">{exact_grid_item['title']}</div>
                                    <div class="card-meta">{exact_grid_item['rating']}</div>
                                </div>
                            </div>
                        </a>
                        """), unsafe_allow_html=True)
                        
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"### Movies related to {exact_movie['title']}")
                    st.markdown("---")
                    
                    recs = recommend(exact_movie['title'])
                    display_movies_grid(recs)
                    
                else:
                    mask = movies['title'].str.contains(query, case=False, regex=False, na=False)
                    results = movies[mask]
                    if not results.empty:
                         with ThreadPoolExecutor(max_workers=3) as executor:
                            movies_to_show = list(executor.map(process_grid_item, [row for _, row in results.head(20).iterrows()]))
                         st.markdown(f"### Results for: {query}")
                         display_movies_grid(movies_to_show)
                    else:
                        st.info("No movies found.")
            
            elif q_type == 'director':
                sub_df = movies[movies['director'].apply(lambda x: query in x if x else False)]
                with ThreadPoolExecutor(max_workers=3) as executor:
                    movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                st.markdown(f"### Director: {query}")
                display_movies_grid(movies_to_show)
            
            elif q_type == 'actor':
                sub_df = movies[movies['top_cast'].apply(lambda x: query in x if isinstance(x, list) else False)]
                with ThreadPoolExecutor(max_workers=3) as executor:
                    movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                st.markdown(f"### Actor: {query}")
                display_movies_grid(movies_to_show)

        elif st.session_state.page == 'watchlist':
            title_text = "❤️ My Watchlist"; wl = get_watchlist(st.session_state.username)
            if not wl.empty:
                sub_df = movies[movies['title'].isin(wl['movie'])]
                with ThreadPoolExecutor(max_workers=3) as executor:
                    movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                st.markdown(f"### {title_text}")
                display_movies_grid(movies_to_show)
            else: st.info("Watchlist is empty.")
        
        elif st.session_state.page == 'liked':
            title_text = "👍 Liked Movies"; lk = get_liked_movies(st.session_state.username)
            if not lk.empty:
                sub_df = movies[movies['title'].isin(lk['movie'])]
                with ThreadPoolExecutor(max_workers=3) as executor:
                    movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                st.markdown(f"### {title_text}")
                display_movies_grid(movies_to_show)
            else: st.info("No liked movies yet.")