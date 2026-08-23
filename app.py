import streamlit as st
import PIL.Image
from google import genai
import firebase_admin
from firebase_admin import credentials, firestore

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

# Sidebar Navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a section", ["AI Recipe & Waste Scanner", "Community Food Board"])

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

elif app_mode == "Community Food Board":
    st.title("🤝 Community Food Rescue Board")
    st.write("Share surplus food with your local community or browse available items to rescue and prevent waste.")

    # Form to list surplus food
    with st.form("food_listing_form"):
        st.subheader("List Surplus Food")
        food_item = st.text_input("Food Item / Description")
        quantity = st.text_input("Quantity / Servings")
        location = st.text_input("Pickup Location / Area")
        contact = st.text_input("Contact Info (Email / Phone)")
        submitted = st.form_submit_button("Post Listing")

        if submitted:
            if food_item and location:
                if db:
                    try:
                        db.collection("surplus_food").add({
                            "food_item": food_item,
                            "quantity": quantity,
                            "location": location,
                            "contact": contact,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.success("Food listing posted successfully!")
                    except Exception as e:
                        st.error(f"Failed to save to database: {e}")
                else:
                    st.success(f"Successfully recorded listing: {food_item} ({quantity}) at {location}! (Configure Firebase secrets to make this persistent across users).")
            else:
                st.warning("Please fill out at least the Food Item and Location fields.")

    st.divider()
    st.subheader("Available Food Listings")
    
    # Display listings from Firestore if connected
    if db:
        try:
            docs = db.collection("surplus_food").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
            listings = list(docs)
            if not listings:
                st.info("No surplus food listed yet. Be the first to share!")
            for doc in listings:
                data = doc.to_dict()
                with st.container(border=True):
                    st.markdown(f"**Item:** {data.get('food_item', 'N/A')}")
                    st.write(f"**Quantity:** {data.get('quantity', 'N/A')}")
                    st.write(f"**Location:** {data.get('location', 'N/A')}")
                    st.write(f"**Contact:** {data.get('contact', 'N/A')}")
        except Exception as e:
            st.warning("Could not fetch listings from Firestore. Please verify your Firebase configuration.")
    else:
        st.info("Firebase is not connected yet. Add your Firebase credentials to Streamlit Secrets to enable live community board posts.")
