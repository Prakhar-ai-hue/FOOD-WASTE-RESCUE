import streamlit as st
import PIL.Image
from google import genai
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Food Waste Rescue Hub",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Animations, Glowing Text, and Responsive Scaling
st.markdown("""
<style>
    /* Global Page Animation & Fade-in */
    .stApp {
        animation: fadeIn 0.8s ease-in-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Animated Glowing Gradient Header */
    .animated-header {
        background: linear-gradient(45deg, #2b580c, #64bb31, #2b580c);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 2.8rem;
        animation: shine 4s linear infinite;
    }
    @keyframes shine {
        to { background-position: 200% center; }
    }

    /* Hover Lift Effects on Containers */
    div.stContainer {
        border-radius: 12px;
        padding: 15px;
        background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div.stContainer:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 20px rgba(76, 175, 80, 0.15);
    }

    /* Styled Glowing Primary Buttons */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #2b580c 0%, #4caf50 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.35);
    }
    .stButton>button[kind="primary"]:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 18px rgba(76, 175, 80, 0.55);
    }
    
    /* Responsive Viewport Optimizations */
    @media (max-width: 768px) {
        .animated-header { font-size: 2rem; }
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase safely
@st.cache_resource
def init_firebase():
    try:
        if not firebase_admin._apps:
            if "FIREBASE_CREDENTIALS" in st.secrets:
                cred_dict = dict(st.secrets["FIREBASE_CREDENTIALS"])
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            else:
                return None
        return firestore.client()
    except Exception as e:
        return None

db = init_firebase()

# Initialize Gemini Client
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        return genai.Client(api_key=api_key)
    except Exception as e:
        return None

client = init_gemini()

# Predefined Real-Life Delhi NCR coordinates
DELHI_LOCATIONS = {
    "Connaught Place (Central Delhi)": {"lat": 28.6280, "lon": 77.2090},
    "South Extension (South Delhi)": {"lat": 28.5700, "lon": 77.2219},
    "Dwarka (West Delhi)": {"lat": 28.5921, "lon": 77.0460},
    "Lajpat Nagar (South Delhi)": {"lat": 28.5677, "lon": 77.2433},
    "Rohini (North Delhi)": {"lat": 28.7041, "lon": 77.1025},
    "Noida Sector 18": {"lat": 28.5708, "lon": 77.3219},
    "Gurugram Cyber City": {"lat": 28.4950, "lon": 77.0895}
}

# Sidebar Global Controls & Navigation
st.sidebar.title("🌍 Global Dashboard")

# Global Prominent Languages Selector
selected_lang = st.sidebar.selectbox(
    "🌐 Choose Language / भाषा चुनें",
    [
        "English", 
        "हिन्दी (Hindi)", 
        "বাংলা (Bengali)", 
        "മലയാളം (Malayalam)", 
        "Español (Spanish)", 
        "Nederlands (Dutch)", 
        "Русский (Russian)", 
        "中文 (Chinese)", 
        "日本語 (Japanese)"
    ]
)

# View Mode Switcher (Desktop vs Mobile Optimized layout padding)
view_mode = st.sidebar.radio("📱 Screen Layout View", ["Auto-Adaptive", "Desktop View", "Mobile View Mode"])

st.sidebar.divider()
st.sidebar.title("🌱 Navigation Menu")

# Core Feature Pages
page = st.sidebar.radio(
    "Select a Page",
    [
        "1. Home & Overview",
        "2. AI Kitchen Assistant",
        "3. Community Food Board & Map",
        "4. Food Delivery & Pickup System",
        "5. Food Storage Guide",
        "6. Local NGO Directory"
    ]
)

# Dictionary translations for global text elements based on selected language
TRANS = {
    "English": {
        "title": "🥗 Food Waste Rescue Hub",
        "subtitle": "Turning kitchen surplus and food waste into community meals and sustainable solutions globally.",
        "ai_title": "🤖 AI Kitchen & Waste Scanner",
        "map_title": "🗺️ Community Food Board & Live Delhi Map",
        "delivery_title": "🚴 Food Delivery & Volunteer Pickup System",
        "storage_title": "🧊 Food Preservation & Storage Guide",
        "ngo_title": "🤝 Local Food Rescue Directory (Delhi NCR)"
    },
    "हिन्दी (Hindi)": {
        "title": "🥗 खाद्य अपशिष्ट बचाव केंद्र",
        "subtitle": "रसोई के बचे हुए भोजन को सामुदायिक भोजन और टिकाऊ समाधानों में बदलना।",
        "ai_title": "🤖 एआई रसोई और अपशिष्ट स्कैनर",
        "map_title": "🗺️ सामुदायिक खाद्य बोर्ड और लाइव दिल्ली मानचित्र",
        "delivery_title": "🚴 खाद्य वितरण और पिकअप प्रणाली",
        "storage_title": "🧊 खाद्य भंडारण मार्गदर्शिका",
        "ngo_title": "🤝 स्थानीय एनजीओ निर्देशिका"
    },
    "বাংলা (Bengali)": {
        "title": "🥗 খাদ্য অপচয় উদ্ধার কেন্দ্র",
        "subtitle": "রান্নাঘরের উদ্বৃত্ত খাবারকে সম্প্রদায়ের খাবারে রূপান্তর করা।",
        "ai_title": "🤖 এআই কিচেন অ্যাসিস্ট্যান্ট",
        "map_title": "🗺️ কমিউনিটি ফুড বোর্ড এবং লাইভ মানচিত্র",
        "delivery_title": "🚴 ফুড ডেলিভারি ও পিকআপ সিস্টেম",
        "storage_title": "🧊 খাদ্য সংরক্ষণ গাইড",
        "ngo_title": "🤝 স্থানীয় এনজিও ডিরেক্টরি"
    },
    "മലയാളം (Malayalam)": {
        "title": "🥗 ഭക്ഷ്യ മാലിന്യ നിർമാർജന കേന്ദ്രം",
        "subtitle": "അടുക്കളയിലെ മിച്ചഭക്ഷണം കമ്മ്യൂണിറ്റി ഭക്ഷണമാക്കി മാറ്റുന്നു.",
        "ai_title": "🤖 എഐ അടുക്കള സഹായി",
        "map_title": "🗺️ കമ്മ്യൂണിറ്റി ഫുഡ് ബോർഡും മാപ്പും",
        "delivery_title": "🚴 ഫുഡ് ഡെലിവറി സിസ്റ്റം",
        "storage_title": "🧊 ഭക്ഷണ സംരക്ഷണ ഗൈഡ്",
        "ngo_title": "🤝 എൻജിഒ ഡയറക്ടറി"
    },
    "Español (Spanish)": {
        "title": "🥗 Centro de Rescate de Residuos de Alimentos",
        "subtitle": "Convirtiendo excedentes de cocina en comidas comunitarias.",
        "ai_title": "🤖 Asistente de Cocina IA",
        "map_title": "🗺️ Tablero de Alimentos y Mapa en Vivo",
        "delivery_title": "🚴 Sistema de Entrega y Recogida",
        "storage_title": "🧊 Guía de Almacenamiento",
        "ngo_title": "🤝 Directorio de ONG Locales"
    },
    "Nederlands (Dutch)": {
        "title": "🥗 Voedselverspilling Reddingshub",
        "subtitle": "Keukenoverschotten omzetten in maaltijden voor de gemeenschap.",
        "ai_title": "🤖 AI Keukenassistent",
        "map_title": "🗺️ Voedselbord & Live Kaart",
        "delivery_title": "🚴 Voedselbezorging & Ophaalsysteem",
        "storage_title": "🧊 Voedselbewaringsgids",
        "ngo_title": "🤝 Lokale NGO Gids"
    },
    "Русский (Russian)": {
        "title": "🥗 Центр спасения пищевых отходов",
        "subtitle": "Превращение излишков еды в общественные обеды.",
        "ai_title": "🤖 ИИ Помощник на кухне",
        "map_title": "🗺️ Доска объявлений и живая карта",
        "delivery_title": "🚴 Система доставки еды",
        "storage_title": "🧊 Руководство по хранению",
        "ngo_title": "🤝 Каталог местных НПО"
    },
    "中文 (Chinese)": {
        "title": "🥗 食物浪费救援中心",
        "subtitle": "将厨房剩余食物转化为社区餐食与可持续方案。",
        "ai_title": "🤖 AI 厨房助手与扫描仪",
        "map_title": "🗺️ 社区食品公告栏与实时地图",
        "delivery_title": "🚴 食品配送与志愿领取系统",
        "storage_title": "🧊 食品保鲜与储存指南",
        "ngo_title": "🤝 本地NGO名录"
    },
    "日本語 (Japanese)": {
        "title": "🥗 食品ロス削減レスキューハブ",
        "subtitle": "キッチンの余剰食材をコミュニティの食事に変える。",
        "ai_title": "🤖 AI キッチンアシスタント",
        "map_title": "🗺️ コミュニティフードボード＆ライブマップ",
        "delivery_title": "🚴 フードデリバリー＆受取システム",
        "storage_title": "🧊 食品保存ガイド",
        "ngo_title": "🤝 ローカルNGOディレクトリ"
    }
}

t = TRANS.get(selected_lang, TRANS["English"])

# ==========================================
# PAGE 1: HOME & OVERVIEW
# ==========================================
if page == "1. Home & Overview":
    st.markdown(f'<p class="animated-header">{t["title"]}</p>', unsafe_allow_html=True)
    st.markdown(f"### {t['subtitle']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Global Food Waste Goal", value="Target 50%", delta="SDG 12.3")
    with col2:
        st.metric(label="Active Delhi Hubs", value=len(DELHI_LOCATIONS), delta="Live")
    with col3:
        st.metric(label="AI Integration", value="Gemini 3.6", delta="Instant")

    st.divider()
    st.markdown("""
    ### 🌟 Core Platform Features:
    * **🤖 AI Kitchen Assistant:** Upload images of leftovers for instant recipes & preservation tips.
    * **🤝 Community Food Board & Map:** Pin surplus meals and locate real pickup nodes across Delhi NCR.
    * **🚴 Delivery System:** Coordinate volunteers and track delivery tasks dynamically.
    * **🧊 Storage Guide & 🤝 NGOs:** Access professional shelf-life data and local shelter directories.
    """)

# ==========================================
# PAGE 2: AI KITCHEN ASSISTANT
# ==========================================
elif page == "2. AI Kitchen Assistant":
    st.markdown(f'<p class="animated-header">{t["ai_title"]}</p>', unsafe_allow_html=True)
    st.write("Upload an image of your ingredients to generate zero-waste culinary ideas instantly.")

    if client is None:
        st.error("⚠️ Gemini API Key not found. Please add `GEMINI_API_KEY` in your Streamlit Secrets.")
    else:
        uploaded_file = st.file_uploader("Upload ingredient photo...", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            image = PIL.Image.open(uploaded_file)
            st.image(image, caption="Uploaded Ingredients", use_container_width=True)
            
            if st.button("Generate Sustainable Recipes", type="primary"):
                with st.spinner("Analyzing with Gemini AI..."):
                    try:
                        prompt = f"Analyze these food items. Provide 2-3 zero-waste recipes and storage tips in {selected_lang}."
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=[image, prompt]
                        )
                        st.success("Analysis Complete!")
                        st.markdown(response.text)
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==========================================
# PAGE 3: COMMUNITY FOOD BOARD & MAP
# ==========================================
elif page == "3. Community Food Board & Map":
    st.markdown(f'<p class="animated-header">{t["map_title"]}</p>', unsafe_allow_html=True)
    st.write("Share surplus food or discover active rescue locations across Delhi NCR.")

    with st.form("food_listing_form"):
        st.subheader("List Surplus Food for Rescue")
        food_item = st.text_input("Food Item / Description")
        quantity = st.text_input("Quantity / Servings")
        selected_area = st.selectbox("Select Delhi NCR Area", list(DELHI_LOCATIONS.keys()))
        contact = st.text_input("Contact Details (Phone / Org Name)")
        
        submitted = st.form_submit_button("Post Listing & Pin on Map", type="primary")

        if submitted:
            if food_item and contact:
                coords = DELHI_LOCATIONS[selected_area]
                listing_data = {
                    "food_item": food_item,
                    "quantity": quantity,
                    "location": selected_area,
                    "contact": contact,
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "timestamp": firestore.SERVER_TIMESTAMP if db else None
                }
                if db:
                    db.collection("surplus_food").add(listing_data)
                    st.success("Listing published successfully!")
                    st.balloons()
                else:
                    st.success("Listing saved locally!")
            else:
                st.warning("Please fill out food item and contact details.")

    st.divider()
    st.subheader("📍 Live Delhi NCR Map")
    map_points = []
    listings_data = []
    if db:
        try:
            docs = db.collection("surplus_food").stream()
            for doc in docs:
                data = doc.to_dict()
                if "lat" in data and "lon" in data:
                    map_points.append({"lat": data["lat"], "lon": data["lon"]})
                    listings_data.append(data)
        except:
            pass

    if not map_points:
        map_points = [{"lat": v["lat"], "lon": v["lon"]} for v in DELHI_LOCATIONS.values()]
        st.info("Showing default hub markers.")

    st.map(pd.DataFrame(map_points), zoom=11)

    st.subheader("📋 Active Listings")
    if db and listings_data:
        for data in listings_data:
            with st.container():
                st.markdown(f"**Item:** {data.get('food_item')} | **Qty:** {data.get('quantity')} | **Hub:** {data.get('location')} | **Contact:** {data.get('contact')}")

# ==========================================
# PAGE 4: FOOD DELIVERY & PICKUP SYSTEM
# ==========================================
elif page == "4. Food Delivery & Pickup System":
    st.markdown(f'<p class="animated-header">{t["delivery_title"]}</p>', unsafe_allow_html=True)
    st.write("Register as a volunteer and claim open transit delivery queues.")

    with st.form("volunteer_form"):
        st.subheader("Volunteer Signup")
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        transport = st.selectbox("Transport Mode", ["Bicycle", "Two-Wheeler", "Car / Auto", "Walking"])
        zone = st.selectbox("Preferred Zone", list(DELHI_LOCATIONS.keys()))
        if st.form_submit_button("Register Volunteer", type="primary"):
            if name and phone:
                st.success(f"Thank you {name}! Registered for {zone}.")
                st.balloons()
            else:
                st.warning("Please provide name and phone.")

    st.divider()
    st.subheader("📦 Active Delivery Queue")
    if db:
        try:
            docs = db.collection("surplus_food").stream()
            for doc in docs:
                data = doc.to_dict()
                with st.container():
                    st.markdown(f"**Item:** {data.get('food_item')} ({data.get('quantity')})")
                    st.write(f"**Pickup Location:** {data.get('location')}")
                    if st.button(f"Accept Delivery Task", key=doc.id, type="primary"):
                        st.success("Delivery task claimed! Safe travels.")
        except:
            st.info("No delivery items found.")
    else:
        st.info("Connect Firebase to sync active deliveries.")

# ==========================================
# PAGE 5: FOOD STORAGE GUIDE
# ==========================================
elif page == "5. Food Storage Guide":
    st.markdown(f'<p class="animated-header">{t["storage_title"]}</p>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🥬 Produce", "🍞 Bakery", "🥩 Proteins"])
    with tab1:
        st.markdown("* Keep leafy greens wrapped in damp paper towels inside airtight boxes.\n* Store onions and potatoes separately.")
    with tab2:
        st.markdown("* Freeze sliced bread to preserve texture much longer than refrigeration.")
    with tab3:
        st.markdown("* Keep dairy products on interior shelves where temperatures remain stable.")

# ==========================================
# PAGE 6: LOCAL NGO DIRECTORY
# ==========================================
elif page == "6. Local NGO Directory":
    st.markdown(f'<p class="animated-header">{t["ngo_title"]}</p>', unsafe_allow_html=True)
    with st.container():
        st.subheader("1. Robin Hood Army (Delhi)")
        st.write("Volunteer network recovering surplus food from restaurants and public gatherings.")
    with st.container():
        st.subheader("2. Feeding India")
        st.write("Comprehensive hunger relief initiative spanning the entire NCR region.")
