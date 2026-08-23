import streamlit as st
import PIL.Image
from google import genai

# Streamlit Page Setup
st.set_page_config(page_title="Food Waste Rescue", page_icon="🥗", layout="centered")

st.title("🥗 Food Waste Rescue")
st.write("Upload an image of your ingredients or food items to get recipe ideas and waste-reduction tips!")

# Initialize Gemini Client using Streamlit secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("Missing GEMINI_API_KEY in Secrets. Please add it in Streamlit Cloud Advanced Settings.")

# Image Upload Widget
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = PIL.Image.open(uploaded_file)
    st.image(image, caption="Uploaded Food Image", use_container_width=True)
    
    if st.button("Analyze & Get Recipes"):
        with st.spinner("Analyzing ingredients with Gemini..."):
            try:
                # Updated to use gemini-3.6-flash
                prompt = (
                    "Identify the ingredients shown in this image. "
                    "Provide 2-3 quick recipe ideas to prevent food waste, "
                    "including estimated prep time and simple steps."
                )
                
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[image, prompt]
                )
                
                st.success("Analysis Complete!")
                st.markdown("### 📝 Suggested Recipes & Tips")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"Error during AI analysis: {e}")
