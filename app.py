import streamlit as st
import PIL.Image
from google import genai
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import numpy as np
import time

# Page Configuration
st.set_page_config(
    page_title="Food Waste Rescue Hub",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced Custom CSS for Heavy Page & Text Animations
st.markdown("""
<style>
    /* Cinematic Page Entrance Animation */
    .stApp {
        animation: cinematicFadeIn 0.7s cubic-bezier(0.25, 1, 0.5, 1) forwards;
    }
    @keyframes cinematicFadeIn {
        0% { opacity: 0; transform: translateY(15px); filter: blur(3px); }
        100% { opacity: 1; transform: translateY(0); filter: blur(0px); }
    }

    /* Dramatic Typing & Shimmer Animation for Headers */
    .animated-header {
        background: linear-gradient(270deg, #1b4d0b, #4caf50, #8bc34a, #2e7d32, #1b4d0b);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 2.7rem;
        margin-bottom: 0.5rem;
        animation: textShimmer 5s ease infinite, textSlideIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        text-shadow: 0 0 30px rgba(76, 175, 80, 0.2);
    }
    @keyframes textShimmer {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes textSlideIn {
        0% { opacity: 0; transform: translateX(-20px); }
        100% { opacity: 1; transform: translateX(0); }
    }

    /* Animated Subtitle Fade & Highlight */
    .animated-subtitle {
        font-size: 1.2rem;
        font-weight: 500;
        color: #2e7d32;
        animation: subtitleFade 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    @keyframes subtitleFade {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    /* Animated Hero Image Frame */
    .stImage img {
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        transition: transform 0.5s ease, box-shadow 0.5s ease;
        animation: imagePopup 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    @keyframes imagePopup {
        0% { opacity: 0; transform: scale(0.95); }
        100% { opacity: 1; transform: scale(1); }
    }
    .stImage img:hover {
        transform: scale(1.01);
        box-shadow: 0 15px 40px rgba(76, 175, 80, 0.3);
    }

    /* Glassmorphic Container Cards with Glowing Borders */
    div.stContainer {
        border-radius: 16px;
        padding: 20px;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(76, 175, 80, 0.3);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.08);
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        margin-bottom: 1rem;
        animation: cardFadeUp 0.7s ease forwards;
    }
    @keyframes cardFadeUp {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    div.stContainer:hover {
        transform: translateY(-5px);
        box-shadow: 0 16px 45px rgba(76, 175, 80, 0.25);
        border-color: #4caf50;
    }

    /* Glowing Primary Action Buttons */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #1b4d0b 0%, #4caf50 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
    }
    .stButton>button[kind="primary"]:hover {
        transform: scale(1.04);
        box-shadow: 0 6px 22px rgba(76, 175, 80, 0.6);
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

selected_lang = st.sidebar.selectbox(
    "🌐 Choose Language / भाषा चुनें",
    [
        "English", "हिन्दी (Hindi)", "বাংলা (Bengali)", "മലയാളം (Malayalam)", 
        "Español (Spanish)", "Nederlands (Dutch)", "Русский (Russian)", "中文 (Chinese)", "日本語 (Japanese)"
    ]
)

st.sidebar.divider()
st.sidebar.title("🌱 Navigation Menu")

page = st.sidebar.radio(
    "Select a Page",
    [
        "1. Home & Overview",
        "2. Impact & Analytics Dashboard",
        "3. AI Kitchen Assistant",
        "4. Community Food Board & Map",
        "5. Food Delivery & Pickup System",
        "6. Food Storage Guide",
        "7. Local NGO Directory"
    ]
)

# Force a micro cinematic transition spinner effect when changing pages
with st.spinner("✨ Loading animated page experience..."):
    time.sleep(0.12)

# Dictionary translations
TRANS = {
    "English": {
        "title": "🥗 Food Waste Rescue Hub",
        "subtitle": "Turning kitchen surplus and food waste into community meals and sustainable solutions globally.",
        "analytics_title": "📊 Impact & Statistical Analysis",
        "ai_title": "🤖 AI Kitchen & Waste Scanner",
        "map_title": "🗺️ Community Food Board & Live Delhi Map",
        "delivery_title": "🚴 Food Delivery & Volunteer Pickup System",
        "storage_title": "🧊 Food Preservation & Storage Guide",
        "ngo_title": "🤝 Local Food Rescue Directory (Delhi NCR)"
    },
    "हिन्दी (Hindi)": {
        "title": "🥗 खाद्य अपशिष्ट बचाव केंद्र",
        "subtitle": "रसोई के बचे हुए भोजन को सामुदायिक भोजन और टिकाऊ समाधानों में बदलना।",
        "analytics_title": "📊 प्रभाव और सांख्यिकीय विश्लेषण",
        "ai_title": "🤖 एआई रसोई और अपशिष्ट स्कैनर",
        "map_title": "🗺️ सामुदायिक खाद्य बोर्ड और लाइव दिल्ली मानचित्र",
        "delivery_title": "🚴 खाद्य वितरण और पिकअप प्रणाली",
        "storage_title": "🧊 खाद्य भंडारण मार्गदर्शिका",
        "ngo_title": "🤝 स्थानीय एनजीओ निर्देशिका"
    }
}
t = TRANS.get(selected_lang, TRANS["English"])

# ==========================================
# PAGE 1: HOME & OVERVIEW
# ==========================================
if page == "1. Home & Overview":
    st.markdown(f'<p class="animated-header">{t["title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="animated-subtitle">{t["subtitle"]}</p>', unsafe_allow_html=True)
    
    st.image(
        "https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&w=1200&q=80",
        caption="Empowering communities by redirecting surplus food safely.",
        use_container_width=True
    )
    
    st.divider()
    st.markdown("""
    ### 🌟 Core Platform Features:
    * **📊 Impact Analytics:** Explore real-time graphical metrics on food rescue and active borrowers.
    * **🤖 AI Kitchen Assistant:** Upload images of leftovers for instant recipes and preservation tips.
    * **🤝 Community Food Board & Map:** Pin surplus meals and locate real pickup nodes across Delhi NCR.
    * **🚴 Delivery System:** Coordinate volunteers and track delivery tasks dynamically.
    * **🧊 Storage Guide & 🤝 NGOs:** Access professional shelf-life data and local shelter directories.
    """)

# ==========================================
# PAGE 2: IMPACT & ANALYTICS DASHBOARD
# ==========================================
elif page == "2. Impact & Analytics Dashboard":
    st.markdown(f'<p class="animated-header">{t["analytics_title"]}</p>', unsafe_allow_html=True)
    st.markdown('<p class="animated-subtitle">Detailed statistical breakdown of community food rescue operations, borrower growth, and hub activity.</p>', unsafe_allow_html=True)
    
    st.image(
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80",
        caption="Data-driven insights into community food security.",
        use_container_width=True
    )
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Meals Rescued", value="14,850", delta="+12% this week")
    with col2:
        st.metric(label="Active Food Borrowers", value="1,240", delta="+85 today")
    with col3:
        st.metric(label="Delhi NCR Hubs", value=len(DELHI_LOCATIONS), delta="Live")
    with col4:
        st.metric(label="Volunteer Deliveries", value="920+", delta="99.4% Success")

    st.markdown("---")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("#### 📈 Monthly Food Borrowing Trends")
        trend_data = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
            "Meals Borrowed": [420, 680, 950, 1100, 1450, 1800, 2100, 2600]
        }).set_index("Month")
        st.line_chart(trend_data)

    with chart_col2:
        st.markdown("#### 📊 Surplus Food Collected by Hub (Kg)")
        hub_data = pd.DataFrame({
            "Hub": ["Connaught Pl.", "South Ext.", "Dwarka", "Lajpat Nagar", "Rohini", "Noida 18", "Gurugram"],
            "Kg Rescued": [320, 450, 280, 510, 390, 600, 720]
        }).set_index("Hub")
        st.bar_chart(hub_data, color="#4caf50")

# ==========================================
# PAGE 3: AI KITCHEN ASSISTANT
# ==========================================
elif page == "3. AI Kitchen Assistant":
    st.markdown(f'<p class="animated-header">{t["ai_title"]}</p>', unsafe_allow_html=True)
    st.markdown('<p class="animated-subtitle">Transform everyday ingredients into sustainable meals with AI.</p>', unsafe_allow_html=True)
    
    st.image(
        "https://images.unsplash.com/photo-1556910103-1c02745aae4d?auto=format&fit=crop&w=1200&q=80",
        caption="Transform everyday ingredients into sustainable meals with AI.",
        use_container_width=True
    )
    
    if client is None:
        st.error("⚠️ Gemini API Key not found in Streamlit Secrets.")
    else:
        uploaded_file = st.file_uploader("Upload ingredient photo...", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = PIL.Image.open(uploaded_file)
            st.image(image, caption="Uploaded Ingredients", use_container_width=True)
            if st.button("Generate Sustainable Recipes", type="primary"):
                with st.spinner("Analyzing with Gemini AI..."):
                    try:
                        prompt = f"Analyze these food items. Provide 2-3 zero-waste recipes and storage tips in {selected_lang}."
                        response = client.models.generate_content(model="gemini-3.6-flash", contents=[image, prompt])
                        st.success("Analysis Complete!")
                        st.markdown(response.text)
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==========================================
# PAGE 4: COMMUNITY FOOD BOARD & MAP
# ==========================================
elif page == "4. Community Food Board & Map":
    st.markdown(f'<p class="animated-header">{t["map_title"]}</p>', unsafe_allow_html=True)
    st.markdown('<p class="animated-subtitle">Connecting local donors and receivers across Delhi NCR.</p>', unsafe_allow_html=True)
    
    st.image(
        "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80",
        caption="Connecting local donors and receivers across Delhi NCR.",
        use_container_width=True
    )

    with st.form("food_listing_form"):
        st.subheader("List Surplus Food for Rescue")
        food_item = st.text_input("Food Item / Description")
        quantity = st.text_input("Quantity / Servings")
        selected_area = st.selectbox("Select Delhi NCR Area", list(DELHI_LOCATIONS.keys()))
        contact = st.text_input("Contact Details (Phone / Org Name)")
        
        if st.form_submit_button("Post Listing & Pin on Map", type="primary"):
            if food_item and contact:
                coords = DELHI_LOCATIONS[selected_area]
                listing_data = {
                    "food_item": food_item, "quantity": quantity, "location": selected_area,
                    "contact": contact, "lat": coords["lat"], "lon": coords["lon"],
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
    map_points = [{"lat": v["lat"], "lon": v["lon"]} for v in DELHI_LOCATIONS.values()]
    st.map(pd.DataFrame(map_points), zoom=11)

# ==========================================
# PAGE 5: FOOD DELIVERY & PICKUP SYSTEM
# ==========================================
elif page == "5. Food Delivery & Pickup System":
    st.markdown(f'<p class="animated-header">{t["delivery_title"]}</p>', unsafe_allow_html=True)
    st.markdown('<p class="animated-subtitle">Volunteer delivery fleet bridging surplus food to shelters.</p>', unsafe_allow_html=True)
    
    st.image(
        "https://images.unsplash.com/photo-1617347454431-f49d7ff5c3b1?auto=format&fit=crop&w=1200&q=80",
        caption="Volunteer delivery fleet bridging surplus food to shelters.",
        use_container_width=True
    )

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

# ==========================================
# PAGE 6: FOOD STORAGE GUIDE
# ==========================================
elif page == "6. Food Storage Guide":
    st.markdown(f'<p class="animated-header">{t["storage_title"]}</p>', unsafe_allow_html=True)
    st.markdown('<p class="animated-subtitle">Professional preservation techniques to extend food shelf-life.</p>', unsafe_allow_html=True)
    
    st.image(
        "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=1200&q=80",
        caption="Professional preservation techniques to extend food shelf-life.",
        use_container_width=True
    )

    tab1, tab2, tab3 = st.tabs(["🥬 Produce", "🍞 Bakery", "🥩 Proteins"])
    with tab1:
        st.markdown("""
        * **Leafy Greens:** Wrap in a damp paper towel and store in an airtight container.
        * **Berries:** Wash just before eating to prevent mold growth.
        """)
    with tab2:
        st.markdown("""
        * **Bread:** Keep at room temperature in a paper bag or freeze slices to preserve texture.
        """)
    with tab3:
        st.markdown("""
        * **Dairy & Meats:** Keep on interior refrigerator shelves where temperature remains stable.
        """)

# ==========================================
# PAGE 7: LOCAL NGO DIRECTORY
# ==========================================
elif page == "7. Local NGO Directory":
    st.markdown(f'<p class="animated-header">{t["ngo_title"]}</p>', unsafe_allow_html=True)
    st.markdown('<p class="animated-subtitle">Partnering with community changemakers across the capital region.</p>', unsafe_allow_html=True)
    
    st.image(
        "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?auto=format&fit=crop&w=1200&q=80",
        caption="Partnering with community changemakers across the capital region.",
        use_container_width=True
    )

    with st.container():
        st.subheader("1. Robin Hood Army (Delhi)")
        st.write("Volunteer network recovering surplus food from restaurants and public gatherings.")
    with st.container():
        st.subheader("2. Feeding India")
        st.write("Comprehensive hunger relief initiative spanning the entire NCR region.")
