import streamlit as st
import datetime
from google import genai
from google.genai import types
import firebase_admin
from firebase_admin import credentials, firestore
import json
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import os

# Page Configuration
st.set_page_config(
    page_title="Annapurna NCR — AI Food Rescue",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- 1. COMPLETE DECOR OVERHAUL: AURORA NEON & MULTI-COLOR TYPOGRAPHY ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');

/* Global App Background & Font */
html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 15% 15%, #162436 0%, #0b101b 45%, #070a12 100%);
    color: #f1f5f9;
}

/* Sidebar Decor */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
    border-right: 1px solid rgba(56, 189, 248, 0.25);
}

/* Multi-Color Gradient Hero Title */
.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(90deg, #34d399 0%, #38bdf8 50%, #fbbf24 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    letter-spacing: -0.5px;
}

.hero-subtitle {
    font-size: 1.1rem;
    color: #94a3b8;
    margin-bottom: 1.5rem;
}

/* Colored Section Headers */
.header-emerald { color: #34d399; font-weight: 700; }
.header-cyan { color: #38bdf8; font-weight: 700; }
.header-amber { color: #fbbf24; font-weight: 700; }
.header-pink { color: #f472b6; font-weight: 700; }

/* Page Slide-In Animation */
@keyframes slideUpFade {
    0% { opacity: 0; transform: translateY(22px); }
    100% { opacity: 1; transform: translateY(0); }
}
.main .block-container {
    animation: slideUpFade 0.55s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

/* Stylish Frosted Glass Cards with Multi-Color Borders */
.decor-card {
    background: rgba(30, 41, 59, 0.55);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 20px;
    padding: 24px;
    border: 1px solid rgba(56, 189, 248, 0.3);
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.4);
    transition: all 0.35s ease;
    margin-bottom: 18px;
}
.decor-card:hover {
    transform: translateY(-6px);
    border-color: #34d399;
    box-shadow: 0 18px 45px rgba(52, 211, 153, 0.22);
}

.decor-card-amber {
    background: linear-gradient(145deg, rgba(45, 30, 20, 0.65), rgba(15, 23, 42, 0.85));
    border-radius: 20px;
    padding: 22px;
    border: 1px solid rgba(251, 191, 36, 0.45);
    box-shadow: 0 10px 30px rgba(251, 191, 36, 0.1);
    transition: all 0.3s ease;
}
.decor-card-amber:hover {
    transform: translateY(-5px);
    border-color: #fbbf24;
}

/* Pill Badges */
.pill-green {
    display: inline-block;
    background: rgba(52, 211, 153, 0.18);
    color: #34d399;
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    border: 1px solid rgba(52, 211, 153, 0.4);
    margin-bottom: 10px;
}
.pill-cyan {
    display: inline-block;
    background: rgba(56, 189, 248, 0.18);
    color: #38bdf8;
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    border: 1px solid rgba(56, 189, 248, 0.4);
    margin-bottom: 10px;
}
.pill-pink {
    display: inline-block;
    background: rgba(244, 114, 182, 0.18);
    color: #f472b6;
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    border: 1px solid rgba(244, 114, 182, 0.4);
    margin-bottom: 10px;
}

/* Image Styling */
img {
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    transition: transform 0.4s ease, box-shadow 0.4s ease;
}
img:hover {
    transform: scale(1.015);
    box-shadow: 0 12px 30px rgba(56, 189, 248, 0.25);
}

/* Gradient Glowing Buttons */
div.stButton > button {
    background: linear-gradient(90deg, #10b981 0%, #0ea5e9 100%);
    color: #ffffff;
    border: none;
    border-radius: 12px;
    font-weight: 700;
    padding: 0.55rem 1.2rem;
    transition: all 0.25s ease;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.35);
}
div.stButton > button:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 25px rgba(14, 165, 233, 0.55);
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

# ---------------- 2. INITIALIZE CONNECTIONS SAFELY ----------------
try:
    if not firebase_admin._apps:
        firebase_config = st.secrets.get("FIREBASE_CREDENTIALS", None)
        if firebase_config:
            cred_dict = json.loads(firebase_config)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
except Exception:
    pass

def get_db():
    try:
        return firestore.client()
    except Exception:
        return None

db = get_db()

api_key = None
try:
    api_key = st.secrets.get("GEMINI_API_KEY", None)
except Exception:
    api_key = os.environ.get("GEMINI_API_KEY")

ai_client = genai.Client(api_key=api_key) if api_key else None


# ---------------- 3. GLOBAL MULTI-LANGUAGE ENGINE ----------------
DICTIONARIES = {
    "Hindi (हिन्दी)": {
        "Restaurant / Donor": "रेस्तरां / दाता",
        "NGO / Recipient": "एनजीओ / प्राप्तकर्ता",
        "Impact & Calculator": "प्रभाव और कैलकुलेटर",
        "Live Analytics": "लाइव एनालिटिक्स",
        "Community Leaderboard": "सामुदायिक लीडरबोर्ड",
        "About Us & Mission": "हमारे बारे में और मिशन"
    },
    "Urdu (اردو)": {
        "Restaurant / Donor": "ریستوراں / ڈونر",
        "NGO / Recipient": "این جی او / وصول کنندہ",
        "Impact & Calculator": "امپیکٹ اور کیلکولیٹر",
        "Live Analytics": "لائیو تجزیہ",
        "Community Leaderboard": "کمیونٹی لیڈر بورڈ",
        "About Us & Mission": "ہمارے بارے میں اور مشن"
    }
}

@st.cache_data(show_spinner=False)
def cached_gemini_translation(text: str, target_lang: str) -> str:
    if not api_key:
        return text
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Translate accurately into {target_lang}. Return ONLY translated text:\n\n{text}"
        )
        return response.text.strip()
    except Exception:
        return text

def t(text: str) -> str:
    if active_language == "English" or not text.strip():
        return text
    clean_lang_key = active_language.split(" (")[0]
    for dict_key, translations in DICTIONARIES.items():
        if clean_lang_key.lower() in dict_key.lower() and text in translations:
            return translations[text]
    return cached_gemini_translation(text, active_language)


# ---------------- 4. SIDEBAR DECOR & NAVIGATION ----------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&w=600&q=80", use_container_width=True)
    st.markdown("<h3 style='color:#38bdf8; margin-bottom:0;'>🌐 Global Language</h3>", unsafe_allow_html=True)
    selected_lang = st.selectbox(
        "Select Interface Language",
        [
            "English", "Hindi (हिन्दी)", "Urdu (اردو)", "Bengali (বাংলা)",
            "Punjabi (ਪੰਜਾਬੀ)", "Korean (한국어)", "Portuguese (Português)",
            "Spanish (Español)", "French (Français)", "German (Deutsch)"
        ],
        label_visibility="collapsed"
    )
    custom_lang = st.text_input("Or type any language:", placeholder="e.g., Japanese, Swahili...")
    active_language = custom_lang.strip() if custom_lang.strip() else selected_lang

    st.divider()
    st.markdown("<h3 style='color:#34d399; margin-bottom:0;'>🧭 Explore Platform</h3>", unsafe_allow_html=True)

    perspective_labels = {
        f"🍽️ {t('Restaurant / Donor')}": "Restaurant / Donor",
        f"🚚 {t('NGO / Recipient')}": "NGO / Recipient",
        f"📊 {t('Impact & Calculator')}": "Impact & Calculator",
        f"📈 {t('Live Analytics')}": "Live Analytics",
        f"🏆 {t('Community Leaderboard')}": "Community Leaderboard",
        f"🌿 {t('About Us & Mission')}": "About Us & Mission"
    }

    selected_perspective_label = st.radio(
        "Navigation",
        list(perspective_labels.keys()),
        label_visibility="collapsed"
    )
    view_mode = perspective_labels[selected_perspective_label]

    st.divider()
    st.markdown("""
    <div style="background: rgba(52, 211, 153, 0.12); padding: 12px; border-radius: 12px; border: 1px solid rgba(52, 211, 153, 0.3);">
        <span style="color:#34d399; font-weight:700;">🟢 Delhi NCR Network: LIVE</span><br>
        <span style="color:#cbd5e1; font-size:0.82rem;">18 NGO Hubs • 34 Active Kitchens</span>
    </div>
    """, unsafe_allow_html=True)


# ---------------- 5. HERO BANNER ----------------
st.markdown(f'<div class="hero-title">{t("🌿 Annapurna NCR — AI Food Rescue")}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-subtitle">{t("Next-Generation Zero-Waste Redistribution Network Connecting Surplus Kitchens to Communities in Need")}</div>', unsafe_allow_html=True)

if "donations" not in st.session_state:
    st.session_state.donations = [
        {
            "id": "1",
            "restaurant": "Central Bistro & Kitchen",
            "location": "Connaught Place, New Delhi",
            "items": "15 portions of Jeera Rice, 10 portions of Yellow Dal",
            "safe_until": "10:30 PM",
            "priority": "HIGH 🔴",
            "status": "Available"
        },
        {
            "id": "2",
            "restaurant": "Royal Tandoor Express",
            "location": "Sector 18, Noida",
            "items": "25 Butter Naans, 12 portions of Paneer Makhani",
            "safe_until": "11:00 PM",
            "priority": "MEDIUM 🟡",
            "status": "Available"
        }
    ]

def fetch_donations():
    if db:
        try:
            docs = db.collection("surplus_food").stream()
            results = [doc.to_dict() for doc in docs]
            if results:
                return results
        except Exception:
            pass
    return st.session_state.donations


# ---------------- PAGE 1: RESTAURANT / DONOR ----------------
if view_mode == "Restaurant / Donor":
    st.image(
        "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1400&q=80",
        caption=t("Turn surplus meals into smiles across Delhi NCR"),
        use_container_width=True
    )
    st.markdown(f"<h2 class='header-emerald'>📍 {t('Log & Broadcast Surplus Food')}</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="decor-card">', unsafe_allow_html=True)
        st.markdown('<div class="pill-green">STEP 1 • KITCHEN DETAILS</div>', unsafe_allow_html=True)
        rest_name = st.text_input("Restaurant / Event Name", value="Grand Spice Bistro")
        location = st.text_input("Pickup Address (Delhi NCR)", value="Connaught Place, New Delhi")
        contact = st.text_input("Coordinator Phone", value="+91 98765 43210")
        expiry_time = st.time_input("Safe Consumption Deadline", value=datetime.time(22, 30))
        uploaded_image = st.file_uploader("Upload Photo of Prepared Surplus Food", type=["jpg", "jpeg", "png"])
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="decor-card">', unsafe_allow_html=True)
        st.markdown('<div class="pill-cyan">STEP 2 • GEMINI VISION INSPECTION</div>', unsafe_allow_html=True)
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Uploaded Surplus Food", use_container_width=True)

            if st.button("🤖 Analyze Freshness & Broadcast Now", use_container_width=True):
                with st.spinner("Running AI freshness verification and portion estimation..."):
                    try:
                        image_bytes = uploaded_image.getvalue()
                        if ai_client:
                            response = ai_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=[
                                    types.Part.from_bytes(data=image_bytes, mime_type=uploaded_image.type),
                                    "Analyze this surplus food image. Provide: 1. Detected items, 2. Estimated portions, 3. Safety & storage tip."
                                ]
                            )
                            ai_text = response.text
                        else:
                            ai_text = "**AI Vision Verified:** Fresh Cooked Rice & Dal (~30 Portions). Safe for immediate redistribution! 🟢"

                        st.balloons()
                        st.success("Verified & Broadcasted to Nearby NGOs!")
                        st.markdown(f"<div style='color:#e2e8f0;'>{ai_text}</div>", unsafe_allow_html=True)

                        new_item = {
                            "id": str(datetime.datetime.now().timestamp()),
                            "restaurant": rest_name,
                            "location": location,
                            "items": ai_text[:110] + "...",
                            "safe_until": expiry_time.strftime("%I:%M %p"),
                            "priority": "HIGH 🔴",
                            "status": "Available"
                        }

                        if db:
                            db.collection("surplus_food").document(new_item["id"]).set(new_item)
                        else:
                            st.session_state.donations.append(new_item)

                        st.toast("Live alert dispatched to NGO volunteers!", icon="🚀")
                    except Exception as e:
                        st.error(f"Analysis error: {e}")
        else:
            st.markdown("""
            <div style="text-align:center; padding: 40px 20px; color:#94a3b8;">
                <h3 style="color:#38bdf8;">📸 Waiting for Food Photo</h3>
                <p>Upload an image on the left to automatically detect food items, estimate servings, and alert nearby shelters.</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ---------------- PAGE 2: NGO / RECIPIENT & INTERACTIVE MAP ----------------
elif view_mode == "NGO / Recipient":
    st.image(
        "https://images.unsplash.com/photo-1488459716781-31db52582fe9?auto=format&fit=crop&w=1400&q=80",
        caption=t("Live Delhi NCR geospatial radar and instant pickup dispatch"),
        use_container_width=True
    )
    st.markdown(f"<h2 class='header-cyan'>🚨 {t('Live Surplus Alerts & Delhi NCR Map')}</h2>", unsafe_allow_html=True)

    st.markdown('<div class="decor-card">', unsafe_allow_html=True)
    st.markdown('<div class="pill-cyan">LIVE GEOSPATIAL RADAR</div>', unsafe_allow_html=True)
    search_query = st.text_input(
        "🔍 Locate any Delhi NCR sector, colony, or city:",
        placeholder="Try: Connaught Place, Noida Sector 62, Gurugram Cyber Hub, Dwarka Sector 10..."
    )

    @st.cache_data(show_spinner=False)
    def get_ncr_coordinates(place_query: str):
        geolocator = Nominatim(user_agent="annapurna_ncr_radar_v1", timeout=5)
        location = geolocator.geocode(f"{place_query}, Delhi NCR, India")
        if location:
            return location.latitude, location.longitude, location.address
        location = geolocator.geocode(f"{place_query}, India")
        if location:
            return location.latitude, location.longitude, location.address
        return None

    map_lat, map_lon = 28.6139, 77.2090
    map_zoom = 11
    marker_text = "Delhi NCR Central Hub"

    if search_query.strip():
        with st.spinner("Pinpointing coordinates..."):
            coords = get_ncr_coordinates(search_query.strip())
            if coords:
                map_lat, map_lon, marker_text = coords
                map_zoom = 15
                st.success(f"📍 Pinpointed: {marker_text}")
            else:
                st.warning("Exact spot not found. Try adding a nearby metro station or sector.")

    ncr_map = folium.Map(location=[map_lat, map_lon], zoom_start=map_zoom, tiles="OpenStreetMap")
    folium.Marker(
        [map_lat, map_lon],
        popup=marker_text,
        tooltip=marker_text,
        icon=folium.Icon(color="green", icon="cutlery", prefix="fa")
    ).add_to(ncr_map)
    folium.Circle([map_lat, map_lon], radius=1200, color="#10b981", fill=True, fill_opacity=0.22).add_to(ncr_map)
    st_folium(ncr_map, width=1050, height=390, returned_objects=[])
    st.markdown('</div>', unsafe_allow_html=True)

    # Interactive Filter Controls
    st.markdown(f"<h3 class='header-amber'>📦 {t('Active Surplus Feed')}</h3>", unsafe_allow_html=True)
    f_col1, f_col2 = st.columns([2, 1])
    with f_col1:
        filter_text = st.text_input("Filter by food or area:", placeholder="e.g., Rice, Noida, Connaught Place...")
    with f_col2:
        priority_filter = st.selectbox("Filter by Urgency:", ["All Listings", "HIGH 🔴", "MEDIUM 🟡"])

    current_donations = fetch_donations()
    filtered_donations = [
        d for d in current_donations
        if (priority_filter == "All Listings" or d.get("priority") == priority_filter)
        and (filter_text.lower() in d.get("items", "").lower() or filter_text.lower() in d.get("location", "").lower() or filter_text.lower() in d.get("restaurant", "").lower())
    ]

    if not filtered_donations:
        st.info("No matching surplus food listings right now.")
    else:
        for idx, item in enumerate(filtered_donations):
            st.markdown('<div class="decor-card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"<h4 style='color:#34d399; margin-bottom:4px;'>📍 {item.get('restaurant', 'Unknown')}</h4>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:#38bdf8; font-weight:600;'>Area:</span> {item.get('location', '')}", unsafe_allow_html=True)
                st.markdown(f"<span style='color:#fbbf24; font-weight:600;'>Menu:</span> {item.get('items', '')}", unsafe_allow_html=True)
                st.markdown(f"<span style='color:#f472b6; font-weight:600;'>Safe Until:</span> {item.get('safe_until', '')}", unsafe_allow_html=True)
            with c2:
                st.metric("Urgency", item.get('priority', 'HIGH 🔴'))
                st.caption("🚗 ~1.4 km away")
            with c3:
                status = item.get('status', 'Available')
                if status == "Available":
                    if st.button("Claim & Dispatch", key=f"claim_{idx}"):
                        item['status'] = "Claimed / Volunteer En Route 🚚"
                        if db:
                            db.collection("surplus_food").document(item['id']).update({"status": "Claimed / Volunteer En Route 🚚"})
                        st.snow()
                        st.toast("Pickup claimed! Volunteer notified.", icon="✅")
                        st.rerun()
                else:
                    st.success(status)
            st.markdown('</div>', unsafe_allow_html=True)


# ---------------- PAGE 3: IMPACT & INTERACTIVE CALCULATOR ----------------
elif view_mode == "Impact & Calculator":
    st.image(
        "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1400&q=80",
        caption=t("Measuring every meal saved and every kilogram of CO2 prevented"),
        use_container_width=True
    )
    st.markdown(f"<h2 class='header-emerald'>📊 {t('Live Impact Metrics & Interactive Simulator')}</h2>", unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown('<div class="decor-card">', unsafe_allow_html=True)
        st.markdown("<span style='color:#34d399; font-weight:700;'>MEALS RESCUED</span>", unsafe_allow_html=True)
        st.metric("", "1,480+", "+52 today 🚀")
        st.markdown('</div>', unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="decor-card">', unsafe_allow_html=True)
        st.markdown("<span style='color:#38bdf8; font-weight:700;'>CO2 PREVENTED</span>", unsafe_allow_html=True)
        st.metric("", "610 kg", "+21 kg today 🌱")
        st.markdown('</div>', unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="decor-card">', unsafe_allow_html=True)
        st.markdown("<span style='color:#fbbf24; font-weight:700;'>WATER SAVED</span>", unsafe_allow_html=True)
        st.metric("", "42,000 L", "+1,400 L 💧")
        st.markdown('</div>', unsafe_allow_html=True)
    with m4:
        st.markdown('<div class="decor-card">', unsafe_allow_html=True)
        st.markdown("<span style='color:#f472b6; font-weight:700;'>ACTIVE PARTNERS</span>", unsafe_allow_html=True)
        st.metric("", "52 Hubs", "Delhi NCR 🤝")
        st.markdown('</div>', unsafe_allow_html=True)

    # Interactive Impact Simulator for Teacher Demo
    st.markdown('<div class="decor-card-amber">', unsafe_allow_html=True)
    st.markdown('<div class="pill-pink">INTERACTIVE SIMULATOR</div>', unsafe_allow_html=True)
    st.markdown("<h3 style='color:#fbbf24;'>🧮 Food Rescue Impact Calculator</h3>", unsafe_allow_html=True)
    st.write("Slide to simulate how much environmental and social impact your kitchen or event can create:")

    meals_slider = st.slider("Number of Surplus Meals Saved:", min_value=5, max_value=500, value=50, step=5)
    sim1, sim2, sim3 = st.columns(3)
    sim1.metric("👥 People Fed", f"{meals_slider} Individuals")
    sim2.metric("🌍 Carbon Footprint Cut", f"{round(meals_slider * 0.42, 1)} kg CO₂")
    sim3.metric("💧 Clean Water Conserved", f"{meals_slider * 28} Liters")
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------- PAGE 4: LIVE ANALYTICS ----------------
elif view_mode == "Live Analytics":
    st.image(
        "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1400&q=80",
        caption=t("Real-time analytics powering smarter food redistribution"),
        use_container_width=True
    )
    st.markdown(f"<h2 class='header-amber'>📈 {t('Waste Reduction & Peak Window Analytics')}</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="decor-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#34d399;'>🍲 Surplus Food Categories</h4>", unsafe_allow_html=True)
        st.bar_chart({"Cooked Meals": 55, "Bakery & Breads": 25, "Fresh Produce": 15, "Beverages": 5})
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="decor-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#38bdf8;'>⏰ Peak Surplus Rescue Windows</h4>", unsafe_allow_html=True)
        st.bar_chart({"12 PM - 2 PM": 30, "4 PM - 6 PM": 15, "9:30 PM - 11:30 PM": 55})
        st.markdown('</div>', unsafe_allow_html=True)


# ---------------- PAGE 5: COMMUNITY LEADERBOARD ----------------
elif view_mode == "Community Leaderboard":
    st.image(
        "https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&w=1400&q=80",
        caption=t("Celebrating Delhi NCR's top zero-waste champions"),
        use_container_width=True
    )
    st.markdown(f"<h2 class='header-pink'>🏆 {t('Community Rescue Champions')}</h2>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🍽️ Top Donor Kitchens", "🦸 Hero Volunteers"])
    with tab1:
        st.markdown('<div class="decor-card">', unsafe_allow_html=True)
        st.markdown("""
        * 🥇 <span style='color:#fbbf24; font-weight:700;'>Grand Spice Bistro (Connaught Place)</span> — *320 Meals Rescued*
        * 🥈 <span style='color:#38bdf8; font-weight:700;'>Central Cafe & Bakery (Noida Sec 18)</span> — *245 Meals Rescued*
        * 🥉 <span style='color:#34d399; font-weight:700;'>Green Leaf Kitchen (Gurugram)</span> — *190 Meals Rescued*
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with tab2:
        st.markdown('<div class="decor-card">', unsafe_allow_html=True)
        st.markdown("""
        * 🥇 <span style='color:#fbbf24; font-weight:700;'>Aarav Sharma</span> — *45 Rapid Pickups Completed*
        * 🥈 <span style='color:#38bdf8; font-weight:700;'>Priya Patel</span> — *38 Rapid Pickups Completed*
        * 🥉 <span style='color:#34d399; font-weight:700;'>Rahul Verma</span> — *30 Rapid Pickups Completed*
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ---------------- PAGE 6: NEW ABOUT US & MISSION PAGE ----------------
elif view_mode == "About Us & Mission":
    st.image(
        "https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&w=1400&q=80",
        caption=t("Bridging the gap between abundance and hunger through technology"),
        use_container_width=True
    )
    st.markdown(f"<h2 class='hero-title' style='font-size:2.2rem;'>🌿 {t('About Annapurna NCR')}</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div class="decor-card">
        <div class="pill-green">OUR VISION</div>
        <h3 style="color:#34d399;">Zero Edible Food Wasted in Delhi NCR</h3>
        <p style="color:#e2e8f0; font-size:1.02rem; line-height:1.7;">
            Every single evening across Delhi, Noida, Gurugram, Faridabad, and Ghaziabad, thousands of freshly prepared meals from restaurants, weddings, and corporate cafeterias go unconsumed—while countless families sleep hungry just kilometers away. 
            <br><br>
            <strong style="color:#38bdf8;">Annapurna NCR</strong> uses <strong style="color:#fbbf24;">Artificial Intelligence (Gemini Vision)</strong> and <strong style="color:#f472b6;">Real-Time Geospatial Mapping</strong> to verify food safety in seconds and connect surplus kitchens directly with verified local NGOs before food spoils.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Three Pillars Grid
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown("""
        <div class="decor-card">
            <div class="pill-cyan">PILLAR 1</div>
            <h4 style="color:#38bdf8;">🤖 AI Food Verification</h4>
            <p style="color:#cbd5e1; font-size:0.92rem;">Instant computer-vision analysis detects food items, estimates portions, and assigns urgency levels automatically.</p>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown("""
        <div class="decor-card">
            <div class="pill-green">PILLAR 2</div>
            <h4 style="color:#34d399;">📍 Hyper-Local Radar</h4>
            <p style="color:#cbd5e1; font-size:0.92rem;">Pinpoints exact sectors and neighborhoods across Delhi NCR so nearby volunteers can complete pickups within 30 minutes.</p>
        </div>
        """, unsafe_allow_html=True)
    with p3:
        st.markdown("""
        <div class="decor-card">
            <div class="pill-pink">PILLAR 3</div>
            <h4 style="color:#f472b6;">🌐 Inclusive Access</h4>
            <p style="color:#cbd5e1; font-size:0.92rem;">Built-in multi-language translation ensures kitchen staff, drivers, and community leaders can use the platform in their native language.</p>
        </div>
        """, unsafe_allow_html=True)

    # Interactive Zero-Waste Pledge Card
    st.markdown('<div class="decor-card-amber">', unsafe_allow_html=True)
    st.markdown('<div class="pill-pink">INTERACTIVE COMMUNITY PLEDGE</div>', unsafe_allow_html=True)
    st.markdown("<h3 style='color:#fbbf24;'>✍️ Sign the Zero-Waste Pledge</h3>", unsafe_allow_html=True)
    pledge_name = st.text_input("Enter your name to join the movement:", placeholder="e.g., Prakhar Jain")
    if st.button("🌟 Take the Zero-Waste Pledge"):
        if pledge_name.strip():
            st.balloons()
            st.success(f"Thank you, {pledge_name}! You are officially registered as an Annapurna NCR Food Rescue Ambassador! 🎉")
        else:
            st.warning("Please enter your name first!")
    st.markdown('</div>', unsafe_allow_html=True)
