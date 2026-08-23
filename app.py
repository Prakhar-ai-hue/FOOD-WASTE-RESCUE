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

# Predefined Delhi coordinates for easy mapping
DELHI_LOCATIONS = {
    "Connaught Place (Central Delhi)": {"lat": 28.6280, "lon": 77.2090},
    "South Extension (South Delhi)": {"lat": 28.5700, "lon": 77.2219},
    "Dwarka (West Delhi)": {"lat": 28.5921, "lon": 77.0460},
    "Lajpat Nagar (South Delhi)": {"lat": 28.5677, "lon": 77.2433},
    "Rohini (North Delhi)": {"lat": 28.7041, "lon": 77.1025},
    "Noida Sector 18": {"lat": 28.5708, "lon": 77.3219},
    "Gurugram Cyber City": {"lat": 28.4950, "lon": 77.0895}
}

# Sidebar Navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a section", ["AI Recipe & Waste Scanner", "Community Food Board & Map"])

if app_mode == "AI Recipe & Waste Scanner":
    st.title("🥗 Food Waste Rescue: AI Kitchen Assistant")
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

elif app_mode == "Community Food Board & Map":
    st.title("🤝 Community Food Rescue Board & Live Map")
    st.write("Share surplus food with your local community or browse real-life pickup locations on the map below to help rescue food from going to waste.")

    # Form to list surplus food with real-life area selection
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
                    st.success(f"Successfully recorded listing for {selected_area}! (Connect Firebase credentials to persist across browser sessions).")
            else:
                st.warning("Please fill out at least the Food Item and Contact details.")

    st.divider()
    st.subheader("📍 Live Food Rescue Map (Delhi NCR)")
    
    # Collect map points from Firestore or show default placeholder pins
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
            
    # Fallback default markers if database is empty so map looks populated
    if not map_points:
        map_points = [{"lat": v["lat"], "lon": v["lon"]} for v in DELHI_LOCATIONS.values()]
        st.info("Showing default hub locations. Post your first real-time food rescue listing above to update the map pins!")
    
    # Display Streamlit Map
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
