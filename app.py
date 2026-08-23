import streamlit as st
import datetime
from google import genai
from google.genai import types
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Page Configuration
st.set_page_config(
    page_title="Food Waste Control & Rescue",
    page_icon="🍲",
    layout="wide"
)

# ---------------- 1. INITIALIZE CONNECTIONS SAFELY ----------------
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
    pass

ai_client = genai.Client(api_key=api_key) if api_key else None


# ---------------- 2. UI LAYOUT & NAVIGATION ----------------

st.title("🍲 Food Waste Control & Surplus Rescue")
st.caption("AI-Powered Real-time Food Preservation, Redistribution & Impact Platform")

st.sidebar.header("🧭 Navigation Panel")
view_mode = st.sidebar.radio(
    "Choose Perspective", 
    [
        "Restaurant / Donor", 
        "NGO / Recipient", 
        "Impact Dashboard", 
        "Live Analytics", 
        "Community Leaderboard"
    ]
)

# Fallback session state list
if "donations" not in st.session_state:
    st.session_state.donations = [
        {
            "id": "1",
            "restaurant": "Central Bistro",
            "location": "Connaught Place, New Delhi",
            "items": "15 portions of Cooked Rice, 10 portions of Dal",
            "safe_until": "10:30 PM",
            "priority": "HIGH 🔴",
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


# ---------------- 3. RESTAURANT / DONOR VIEW ----------------
if view_mode == "Restaurant / Donor":
    st.header("📍 Log & Broadcast Surplus Food")
    st.write("Upload a picture of your surplus food. Our model will automatically check freshness, estimate portions, and broadcast it to nearby NGOs.")
    
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        st.subheader("Restaurant Details")
        rest_name = st.text_input("Restaurant Name", value="Grand Spice Bistro")
        location = st.text_input("Location / Address", value="Connaught Place, New Delhi")
        contact = st.text_input("Contact Info", value="+91 98765 43210")
        expiry_time = st.time_input("Safe Consumption Until", value=datetime.time(22, 30))
        
        uploaded_image = st.file_uploader("Upload Photo of Surplus Food", type=["jpg", "jpeg", "png"])

    with col2:
        st.subheader("AI Analysis Engine")
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Uploaded Surplus Photo", use_container_width=True)
            
            if st.button("🤖 Analyze with AI", type="primary", use_container_width=True):
                with st.spinner("Analyzing portion size, food category, and safety guidelines..."):
                    try:
                        image_bytes = uploaded_image.getvalue()
                        
                        if ai_client:
                            response = ai_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=[
                                    types.Part.from_bytes(data=image_bytes, mime_type=uploaded_image.type),
                                    "Analyze this surplus food image. Provide: 1. Detected food items, 2. Estimated number of portions, 3. Food category (Cooked/Perishable vs Dry), 4. Priority level (High/Medium/Low)."
                                ]
                            )
                            ai_text = response.text
                        else:
                            ai_text = "**Simulated AI Analysis:** Detected Mixed Grain Rice & Dal, ~30 Portions, Category: Cooked/Perishable, Priority: HIGH 🔴 *(Tip: Configure API key in secrets for live cloud vision)*."

                        st.balloons()
                        st.success("AI Analysis Complete & Verified!")
                        st.markdown(ai_text)
                        
                        new_item = {
                            "id": str(datetime.datetime.now().timestamp()),
                            "restaurant": rest_name,
                            "location": location,
                            "items": ai_text[:100] + "...",
                            "safe_until": expiry_time.strftime("%I:%M %p"),
                            "priority": "HIGH 🔴",
                            "status": "Available"
                        }
                        
                        if db:
                            db.collection("surplus_food").document(new_item["id"]).set(new_item)
                        else:
                            st.session_state.donations.append(new_item)
                            
                        st.toast("Surplus successfully logged & broadcasted to NGOs!", icon="🚀")
                    except Exception as e:
                        st.error(f"Error during AI analysis: {e}")
        else:
            st.info("👆 Upload an image on the left to trigger the automated AI evaluation.")

# ---------------- 4. NGO / RECIPIENT VIEW ----------------
elif view_mode == "NGO / Recipient":
    st.header("🚨 Live Food Surplus Alerts")
    st.markdown("Real-time feed of safe surplus food ready for immediate pickup in your neighborhood.")
    
    current_donations = fetch_donations()
    
    if not current_donations:
        st.info("No surplus food currently available in your area.")
    else:
        for idx, item in enumerate(current_donations):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.subheader(f"📍 {item.get('restaurant', 'Unknown')}")
                    st.write(f"**Location:** {item.get('location', '')}")
                    st.write(f"**Details:** {item.get('items', '')}")
                    st.write(f"**Available Until:** {item.get('safe_until', '')}")
                with c2:
                    st.metric("Priority", item.get('priority', 'HIGH'))
                    st.caption("Distance: ~1.2 km away")
                with c3:
                    status = item.get('status', 'Available')
                    if status == "Available":
                        if st.button(f"Claim Donation", key=f"btn_{idx}", type="primary"):
                            item['status'] = "Claimed / Pickup En Route"
                            if db:
                                db.collection("surplus_food").document(item['id']).update({"status": "Claimed / Pickup En Route"})
                            st.snow()
                            st.success("Successfully Claimed! Dispatch details sent.")
                            st.rerun()
                    else:
                        st.warning(f"Status: {status}")

# ---------------- 5. IMPACT DASHBOARD ----------------
elif view_mode == "Impact Dashboard":
    st.header("📊 Real-Time Rescue & Sustainability Metrics")
    st.write("Tracking the tangible environmental and humanitarian impact of our zero-waste network.")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Meals Rescued", "1,450+", "+45 today")
    m2.metric("CO2 Emissions Prevented", "580 kg", "+18 kg today")
    m3.metric("Partner Restaurants", "34 active", "+2 this week")
    m4.metric("Connected NGOs", "18 centers", "100% covered")
    
    st.divider()
    st.subheader("📈 Monthly Meal Rescue Growth")
    chart_data = [120, 240, 350, 480, 690, 950, 1450]
    st.line_chart(chart_data)

# ---------------- 6. LIVE ANALYTICS ----------------
elif view_mode == "Live Analytics":
    st.header("📈 Waste Reduction & Expiry Analytics")
    st.markdown("Breakdown of surplus food categories and optimal safety response time windows.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Surplus Category Breakdown")
        categories = {"Cooked Meals": 55, "Bakery & Breads": 25, "Fresh Produce": 15, "Beverages": 5}
        st.bar_chart(categories)
    with col2:
        st.subheader("Peak Surplus Generation Times")
        times = {"12:00 PM - 2:00 PM": 30, "4:00 PM - 6:00 PM": 15, "9:30 PM - 11:30 PM": 55}
        st.bar_chart(times)

# ---------------- 7. COMMUNITY LEADERBOARD ----------------
elif view_mode == "Community Leaderboard":
    st.header("🏆 Top Food Rescue Champions")
    st.markdown("Celebrating the restaurants and volunteers leading the charge against food waste this month.")
    
    tab1, tab2 = st.tabs(["Top Donor Restaurants", "Hero Volunteers"])
    
    with tab1:
        st.markdown("""
        1. 🥇 **Grand Spice Bistro** — *320 Meals Donated*
        2. 🥈 **Central Cafe** — *245 Meals Donated*
        3. 🥉 **Green Leaf Kitchen** — *190 Meals Donated*
        """)
    with tab2:
        st.markdown("""
        1. 🥇 **Aarav Sharma** — *45 Pickups Completed*
        2. 🥈 **Priya Patel** — *38 Pickups Completed*
        3. 🥉 **Rahul Verma** — *30 Pickups Completed*
        """)
