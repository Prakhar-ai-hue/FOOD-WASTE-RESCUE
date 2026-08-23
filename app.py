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

# Predefined Delhi NCR coordinates for mapping
DELHI_LOCATIONS = {
    "Connaught Place (Central Delhi)": {"lat": 28.6280, "lon": 77.2090},
    "South Extension (South Delhi)": {"lat": 28.5700, "lon": 77.2219},
    "Dwarka (West Delhi)": {"lat": 28.5921, "lon": 77.0460},
    "Lajpat Nagar (South Delhi)": {"lat": 28.5677, "lon": 77.2433},
    "Rohini (North Delhi)": {"lat": 28.7041, "lon": 77.1025},
    "Noida Sector 18": {"lat": 28.5708, "lon": 77.3219},
    "Gurugram Cyber City": {"lat": 28.4950, "lon": 77.0895}
}

# 5-Page Sidebar Navigation
st.sidebar.title("🌱 Navigation Menu")
page = st.sidebar.radio(
    "Select a Page",
    [
        "1. Home & Overview",
        "2. AI Kitchen Assistant",
        "3. Community Food Board & Map",
        "4. Food Storage Guide",
        "5. Local NGO Directory"
    ]
)

# ==========================================
# PAGE 1: HOME & OVERVIEW
# ==========================================
if page == "1. Home & Overview":
    st.title("🥗 Welcome to Food Waste Rescue Hub")
    st.markdown("### Turning kitchen surplus and food waste into community meals and sustainable solutions.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Global Food Waste Reduction", value="Target 50%", delta="SDG 12.3")
    with col2:
        st.metric(label="Active Hubs in Delhi NCR", value=len(DELHI_LOCATIONS), delta="Live")
    with col3:
        st.metric(label="AI Powered Analysis", value="Instant", delta="Gemini 3.6")

    st.divider()
    st.markdown("""
    ### What you can do here:
    * **🤖 AI Kitchen Assistant:** Upload pictures of random ingredients or fridge leftovers to instantly generate recipes and shelf-life extension tricks.
    * **🤝 Community Food Board:** List excess food from events, restaurants, or households, and locate surplus meals on our interactive Delhi map.
    * **🧊 Storage Guide:** Learn how to properly freeze, wrap, and preserve perishable items.
    * **🤝 NGO Directory:** Discover local organizations helping distribute meals across the capital region.
    """)

# ==========================================
# PAGE 2: AI KITCHEN ASSISTANT
# ==========================================
elif page == "2. AI Kitchen Assistant":
    st.title("🤖 AI Kitchen & Waste Scanner")
    st.write("Upload an image of your leftover ingredients or food items to instantly generate sustainable recipes, storage tricks, and waste-reduction solutions.")

    if client is None:
        st.error("⚠️ Gemini API Key not found. Please add `GEMINI_API_KEY` in your Streamlit Secrets.")
    else:
        uploaded_file = st.file_uploader("Upload an image of your food/ingredients...", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            image = PIL.Image.open(uploaded_file)
            st.image(image, caption="Your Uploaded Ingredients", use_container_width=True)
            
            if st.button("Analyze & Get Recipes", type="primary"):
                with st.spinner("Analyzing ingredients with Gemini..."):
                    try:
                        prompt = (
                            "You are an expert chef and food sustainability assistant. "
                            "Analyze the food items shown in this image. "
                            "1. Identify the key ingredients present. "
                            "2. Provide 2-3 delicious, easy-to-make recipe ideas to prevent them from going to waste. "
                            "3. Include storage tips to extend their freshness if they shouldn't be cooked immediately."
                        )
                        
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=[image, prompt]
                        )
                        
                        st.success("Analysis Complete!")
                        st.markdown("### 📝 Suggested Recipes & Tips")
                        st.markdown(response.text)
                        
                    except Exception as e:
                        st.error(f"Error during AI analysis: {e}")

# ==========================================
# PAGE 3: COMMUNITY FOOD BOARD & MAP
# ==========================================
elif page == "3. Community Food Board & Map":
    st.title("🗺️ Community Food Board & Live Delhi Map")
    st.write("Share surplus food with your local community or browse real-life pickup locations on the map below to help rescue food from going to waste.")

    with st.form("food_listing_form"):
        st.subheader("List Surplus Food for Rescue")
        food_item = st.text_input("Food Item / Description (e.g., 10 boxes of fresh sandwiches)")
        quantity = st.text_input("Quantity / Servings (e.g., 15 servings)")
        selected_area = st.selectbox("Select Area / Pickup Hub", list(DELHI_LOCATIONS.keys()))
        contact = st.text_input("Contact Info (Phone / Email / Organization Name)")
        
        submitted = st.form_submit_button("Post Listing & Pin on Map")

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
                    try:
                        db.collection("surplus_food").add(listing_data)
                        st.success("Food listing successfully posted and pinned on the map!")
                    except Exception as e:
                        st.error(f"Failed to save to database: {e}")
                else:
                    st.success(f"Successfully recorded listing for {selected_area}! (Connect Firebase credentials to persist across sessions).")
            else:
                st.warning("Please fill out at least the Food Item and Contact details.")

    st.divider()
    st.subheader("📍 Live Food Rescue Map (Delhi NCR)")
    
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
        except Exception as e:
            st.warning("Could not fetch database records for the map.")
            
    if not map_points:
        map_points = [{"lat": v["lat"], "lon": v["lon"]} for v in DELHI_LOCATIONS.values()]
        st.info("Showing default hub locations. Post your first real-time food rescue listing above to update the map pins!")
    
    df_map = pd.DataFrame(map_points)
    st.map(df_map, zoom=11)

    st.divider()
    st.subheader("📋 Available Food Listings")
    
    if db and listings_data:
        for data in listings_data:
            with st.container(border=True):
                st.markdown(f"**Item:** {data.get('food_item', 'N/A')}")
                st.write(f"**Quantity:** {data.get('quantity', 'N/A')}")
                st.write(f"**Location / Hub:** {data.get('location', 'N/A')}")
                st.write(f"**Contact:** {data.get('contact', 'N/A')}")
    else:
        st.write("Browse active pickup points from the map above or post a listing to get started.")

# ==========================================
# PAGE 4: FOOD STORAGE GUIDE
# ==========================================
elif page == "4. Food Storage Guide":
    st.title("🧊 Food Preservation & Storage Guide")
    st.write("Proper storage is the first line of defense against food waste. Explore these pro-tips to maximize freshness:")

    tab1, tab2, tab3 = st.tabs(["🥬 Vegetables & Fruits", "🍞 Bakery & Grains", "🥩 Dairy & Proteins"])

    with tab1:
        st.subheader("Produce Preservation Tips")
        st.markdown("""
        * **Leafy Greens:** Wrap in a damp paper towel and store in an airtight container to keep them crisp for up to a week.
        * **Berries:** Wash just before eating, not before storing, to prevent mold growth from excess moisture.
        * **Root Vegetables:** Store potatoes and onions in a cool, dark, well-ventilated place—never store them together because onions release gases that accelerate sprouting.
        """)

    with tab2:
        st.markdown("""
        ### Breads & Dry Goods
        * **Bread:** Keep bread at room temperature in a paper bag or bread box. Freezing sliced bread preserves texture much better than refrigeration.
        * **Rice & Grains:** Store in airtight glass or plastic containers in a cool pantry to keep pests out.
        """)

    with tab3:
        st.markdown("""
        ### Meat, Dairy & Leftovers
        * **Dairy:** Keep milk and yogurt on interior refrigerator shelves rather than the door, where temperature fluctuates.
        * **Leftovers:** Consume cooked meals within 3 to 4 days when stored in the fridge, or freeze them immediately for longer storage.
        """)

# ==========================================
# PAGE 5: LOCAL NGO DIRECTORY
# ==========================================
elif page == "5. Local NGO Directory":
    st.title("🤝 Local Food Rescue Directory (Delhi NCR)")
    st.write("Partner with or donate surplus food directly to established organizations operating across Delhi:")

    with st.container(border=True):
        st.subheader("1. Robin Hood Army (Delhi Chapter)")
        st.write("**Mission:** A volunteer-based organization that collects surplus food from restaurants and distributes it to less fortunate citizens.")
        st.write("**Operational Areas:** Pan-Delhi (Connaught Place, South Delhi, Rohini, Dwarka)")

    with st.container(border=True):
        st.subheader("2. Feeding India (Zomato Feeding India)")
        st.write("**Mission:** Direct hunger relief initiative focused on routing surplus food from weddings, corporate cafeterias, and restaurants.")
        st.write("**Operational Areas:** NCR Wide")

    with st.container(border=True):
        st.subheader("3. Local Community Food Banks & Gurdwaras")
        st.write("**Mission:** Community-driven langar services providing massive daily meal distributions.")
        st.write("**Operational Areas:** Major Gurdwaras across Delhi NCR")
