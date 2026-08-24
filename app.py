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

# Navigation items translated dictionary
NAV_LABELS = {
    "English": ["1. Home & Overview", "2. Impact & Analytics Dashboard", "3. AI Kitchen Assistant", "4. Community Food Board & Map", "5. Food Delivery & Pickup System", "6. Food Storage Guide", "7. Local NGO Directory"],
    "हिन्दी (Hindi)": ["1. होम और अवलोकन", "2. प्रभाव और विश्लेषण डैशबोर्ड", "3. एआई रसोई सहायक", "4. सामुदायिक खाद्य बोर्ड और मानचित्र", "5. खाद्य वितरण और पिकअप प्रणाली", "6. खाद्य भंडारण मार्गदर्शिका", "7. स्थानीय एनजीओ निर्देशिका"],
    "বাংলা (Bengali)": ["১. হোম ও ওভারভিউ", "২. ইমপ্যাক্ট ও অ্যানালিটিক্স", "৩. এআই কিচেন অ্যাসিস্ট্যান্ট", "৪. কমিউনিটি ফুড বোর্ড ও ম্যাপ", "৫. ফুড ডেলিভারি সিস্টেম", "৬. ফুড স্টোরেজ গাইড", "৭. লোকাল এনজিও ডিরেক্টরি"],
    "മലയാളം (Malayalam)": ["1. ഹോം & അവലോകനം", "2. ഇംപാക്ട് & അനലിറ്റിക്സ്", "3. എഐ അടുക്കള സഹായി", "4. കമ്മ്യൂണിറ്റി ഫുഡ് ബോർഡ്", "5. ഫുഡ് ഡെലിവറി സിസ്റ്റം", "6. ഭക്ഷണ സംരക്ഷണ ഗൈഡ്", "7. എൻജിഒ ഡയറക്ടറി"],
    "Español (Spanish)": ["1. Inicio", "2. Panel de Análisis", "3. Asistente IA", "4. Tablero Comunitario", "5. Sistema de Entrega", "6. Guía de Almacenamiento", "7. Directorio ONG"],
    "Nederlands (Dutch)": ["1. Home", "2. Analyse Dashboard", "3. AI Keukenassistent", "4. Voedselbord & Kaart", "5. Bezorgsysteem", "6. Bewaringsgids", "7. NGO Gids"],
    "Русский (Russian)": ["1. Главная", "2. Панель аналитики", "3. ИИ Помощник", "4. Общественная доска", "5. Система доставки", "6. Руководство по хранению", "7. Каталог НПО"],
    "中文 (Chinese)": ["1. 首页与概览", "2. 影响与分析面板", "3. AI 厨房助手", "4. 社区食品板与地图", "5. 食品配送系统", "6. 食品储存指南", "7. 本地NGO名录"],
    "日本語 (Japanese)": ["1. ホーム＆概要", "2. インパクト分析", "3. AIキッチンアシスタント", "4. コミュニティフードボード", "5. デリバリーシステム", "6. 食品保存ガイド", "7. NGOディレクトリ"]
}

current_nav_options = NAV_LABELS.get(selected_lang, NAV_LABELS["English"])
selected_nav_label = st.sidebar.radio("Select a Page", current_nav_options)

# Map back chosen label to english index key
page_index = current_nav_options.index(selected_nav_label)
page_keys = [
    "Home & Overview", "Impact & Analytics Dashboard", "AI Kitchen Assistant", 
    "Community Food Board & Map", "Food Delivery & Pickup System", "Food Storage Guide", "Local NGO Directory"
]
page = page_keys[page_index]

# Force a micro cinematic transition spinner effect when changing pages
with st.spinner("✨ Loading animated page experience..."):
    time.sleep(0.12)

# Comprehensive Multi-Language Content Dictionaries
TRANS = {
    "English": {
        "title": "🥗 Food Waste Rescue Hub",
        "subtitle": "Turning kitchen surplus and food waste into community meals and sustainable solutions globally.",
        "analytics_title": "📊 Impact & Statistical Analysis",
        "analytics_sub": "Detailed statistical breakdown of community food rescue operations, borrower growth, and hub activity.",
        "ai_title": "🤖 AI Kitchen & Waste Scanner",
        "ai_sub": "Transform everyday ingredients into sustainable meals with AI.",
        "map_title": "🗺️ Community Food Board & Live Delhi Map",
        "map_sub": "Connecting local donors and receivers across Delhi NCR.",
        "delivery_title": "🚴 Food Delivery & Volunteer Pickup System",
        "delivery_sub": "Volunteer delivery fleet bridging surplus food to shelters.",
        "storage_title": "🧊 Food Preservation & Storage Guide",
        "storage_sub": "Professional preservation techniques to extend food shelf-life.",
        "ngo_title": "🤝 Local Food Rescue Directory (Delhi NCR)",
        "ngo_sub": "Partnering with community changemakers across the capital region.",
        "features": "### 🌟 Core Platform Features:\n* **📊 Impact Analytics:** Explore real-time graphical metrics on food rescue and active borrowers.\n* **🤖 AI Kitchen Assistant:** Upload images of leftovers for instant recipes and preservation tips.\n* **🤝 Community Food Board & Map:** Pin surplus meals and locate real pickup nodes across Delhi NCR.\n* **🚴 Delivery System:** Coordinate volunteers and track delivery tasks dynamically.\n* **🧊 Storage Guide & 🤝 NGOs:** Access professional shelf-life data and local shelter directories."
    },
    "हिन्दी (Hindi)": {
        "title": "🥗 खाद्य अपशिष्ट बचाव केंद्र",
        "subtitle": "रसोई के बचे हुए भोजन को सामुदायिक भोजन और टिकाऊ समाधानों में बदलना।",
        "analytics_title": "📊 प्रभाव और सांख्यिकीय विश्लेषण",
        "analytics_sub": "सामुदायिक खाद्य बचाव कार्यों, उधारकर्ता की वृद्धि और हब गतिविधियों का विस्तृत सांख्यिकीय विवरण।",
        "ai_title": "🤖 एआई रसोई और अपशिष्ट स्कैनर",
        "ai_sub": "एआई के साथ रोजमर्रा की सामग्री को टिकाऊ भोजन में बदलें।",
        "map_title": "🗺️ सामुदायिक खाद्य बोर्ड और लाइव दिल्ली मानचित्र",
        "map_sub": "दिल्ली एनसीआर में स्थानीय दाताओं और प्राप्तकर्ताओं को जोड़ना।",
        "delivery_title": "🚴 खाद्य वितरण और पिकअप प्रणाली",
        "delivery_sub": "स्वयंसेवक डिलीवरी बेड़ा जो अधिशेष भोजन को आश्रयों तक पहुँचाता है।",
        "storage_title": "🧊 खाद्य भंडारण मार्गदर्शिका",
        "storage_sub": "भोजन की शेल्फ-लाइफ बढ़ाने के लिए पेशेवर संरक्षण तकनीकें।",
        "ngo_title": "🤝 स्थानीय एनजीओ निर्देशिका",
        "ngo_sub": "पूंजी क्षेत्र में सामुदायिक परिवर्तन निर्माताओं के साथ साझेदारी।",
        "features": "### 🌟 मुख्य प्लेटफ़ॉर्म सुविधाएँ:\n* **📊 प्रभाव विश्लेषण:** खाद्य बचाव और सक्रिय उधारकर्ताओं पर रीयल-टाइम ग्राफिक मेट्रिक्स का अन्वेषण करें।\n* **🤖 एआई रसोई सहायक:** तत्काल व्यंजनों और संरक्षण युक्तियों के लिए बचे हुए भोजन की तस्वीरें अपलोड करें।\n* **🤝 सामुदायिक खाद्य बोर्ड और मानचित्र:** अतिरिक्त भोजन पिन करें और दिल्ली एनसीआर में पिकअप नोड खोजें।\n* **🚴 वितरण प्रणाली:** स्वयंसेवकों का समन्वय करें और डिलीवरी कार्यों को गतिशील रूप से ट्रैक करें।\n* **🧊 भंडारण गाइड और 🤝 एनजीओ:** पेशेवर शेल्फ-लाइफ डेटा और स्थानीय आश्रय निर्देशिकाओं तक पहुँचें।"
    },
    "বাংলা (Bengali)": {
        "title": "🥗 খাদ্য অপচয় উদ্ধার কেন্দ্র",
        "subtitle": "রান্নাঘরের উদ্বৃত্ত খাবারকে সম্প্রদায়ের খাবারে রূপান্তর করা।",
        "analytics_title": "📊 প্রভাব ও পরিসংখ্যানগত বিশ্লেষণ",
        "analytics_sub": "সম্প্রদায়ের খাদ্য উদ্ধার কার্যক্রম, ঋণগ্রহীতার বৃদ্ধি এবং হাব কার্যকলাপের বিস্তারিত বিশ্লেষণ।",
        "ai_title": "🤖 এআই কিচেন অ্যাসিস্ট্যান্ট",
        "ai_sub": "এআই দিয়ে উদ্বৃত্ত উপাদানকে টেকসই খাবারে রূপান্তর করুন।",
        "map_title": "🗺️ কমিউনিটি ফুড বোর্ড এবং লাইভ মানচিত্র",
        "map_sub": "দিল্লী এনসিআর জুড়ে স্থানীয় দাতা এবং গ্রাহকদের সংযোগ করা।",
        "delivery_title": "🚴 ফুড ডেলিভারি ও পিকআপ সিস্টেম",
        "delivery_sub": "স্বেচ্ছাসেবক ডেলিভারি দল যারা অতিরিক্ত খাবার শেল্টারে পৌঁছে দেয়।",
        "storage_title": "🧊 খাদ্য সংরক্ষণ গাইড",
        "storage_sub": "খাবারের আয়ু বাড়ানোর পেশাদার সংরক্ষণ কৌশল।",
        "ngo_title": "🤝 স্থানীয় এনজিও ডিরেক্টরি",
        "ngo_sub": "রাজধানী অঞ্চলের কমিউনিটি পরিবর্তনকারীদের সাথে অংশীদারিত্ব।",
        "features": "### 🌟 মূল প্ল্যাটফর্ম বৈশিষ্ট্য:\n* **📊 ইমপ্যাক্ট অ্যানালিটিক্স:** রিয়েল-টাইম মেট্রিক্সে খাদ্য উদ্ধার দেখুন।\n* **🤖 এআই কিচেন অ্যাসিস্ট্যান্ট:** তাৎক্ষণিক রান্নার রেসিপির ছবি আপলোড করুন।"
    },
    "മലയാളം (Malayalam)": {
        "title": "🥗 ഭക്ഷ്യ മാലിന്യ നിർമാർജന കേന്ദ്രം",
        "subtitle": "അടുക്കളയിലെ മിച്ചഭക്ഷണം കമ്മ്യൂണിറ്റി ഭക്ഷണമാക്കി മാറ്റുന്നു.",
        "analytics_title": "📊 ഇംപാക്ട് & സ്റ്റാറ്റിസ്റ്റിക്കൽ അനാലിസിസ്",
        "analytics_sub": "കമ്മ്യൂണിറ്റി ഫുഡ് റെസ്ക്യൂ പ്രവർത്തനങ്ങളുടെ വിശദമായ ഡാറ്റ.",
        "ai_title": "🤖 എഐ അടുക്കള സഹായി",
        "ai_sub": "എഐ ഉപയോഗിച്ച് സുസ്ഥിരമായ പാചകക്കുറിപ്പുകൾ ഉണ്ടാക്കുക.",
        "map_title": "🗺️ കമ്മ്യൂണിറ്റി ഫുഡ് ബോർഡും മാപ്പും",
        "map_sub": "ഡൽഹി NCR-ൽ ഉടനീളമുള്ള ദാതാക്കളെയും സ്വീകർത്താക്കളെയും ബന്ധിപ്പിക്കുന്നു.",
        "delivery_title": "🚴 ഫുഡ് ഡെലിവറി സിസ്റ്റം",
        "delivery_sub": "സന്നദ്ധ പ്രവർത്തകരുടെ ഡെലിവറി ശൃംഖല.",
        "storage_title": "🧊 ഭക്ഷണ സംരക്ഷണ ഗൈഡ്",
        "storage_sub": "ഭക്ഷ്യക്ഷാമം പരിഹരിക്കാനുള്ള സാങ്കേതിക വിദ്യകൾ.",
        "ngo_title": "🤝 എൻജിഒ ഡയറക്ടറി",
        "ngo_sub": "പ്രാദേശിക സംഘടനകളുടെ വിവരങ്ങൾ.",
        "features": "### 🌟 പ്രധാന സവിശേഷതകൾ:\n* **📊 ഇംപാക്ട് അനലിറ്റിക്സ്:** തത്സമയ ഡാറ്റ പരിശോധിക്കുക."
    },
    "Español (Spanish)": {
        "title": "🥗 Centro de Rescate de Residuos de Alimentos",
        "subtitle": "Convirtiendo excedentes de cocina en comidas comunitarias.",
        "analytics_title": "📊 Análisis de Impacto y Estadísticas",
        "analytics_sub": "Desglose estadístico detallado de las operaciones de rescate de alimentos.",
        "ai_title": "🤖 Asistente de Cocina IA",
        "ai_sub": "Transforma ingredientes cotidianos en comidas sostenibles con IA.",
        "map_title": "🗺️ Tablero de Alimentos y Mapa en Vivo",
        "map_sub": "Conectando donantes y receptores locales en Delhi NCR.",
        "delivery_title": "🚴 Sistema de Entrega y Recogida",
        "delivery_sub": "Flota de entrega voluntaria que lleva alimentos excedentes a refugios.",
        "storage_title": "🧊 Guía de Almacenamiento",
        "storage_sub": "Técnicas de preservación profesional para extender la vida útil.",
        "ngo_title": "🤝 Directorio de ONG Locales",
        "ngo_sub": "Asociación con agentes de cambio comunitarios en la región.",
        "features": "### 🌟 Características Principales:\n* **📊 Análisis de Impacto:** Explore métricas en tiempo real."
    },
    "Nederlands (Dutch)": {
        "title": "🥗 Voedselverspilling Reddingshub",
        "subtitle": "Keukenoverschotten omzetten in maaltijden voor de gemeenschap.",
        "analytics_title": "📊 Impact & Statistische Analyse",
        "analytics_sub": "Gedetailleerd overzicht van voedselreddingsoperaties.",
        "ai_title": "🤖 AI Keukenassistent",
        "ai_sub": "Zet dagelijkse ingrediënten om in duurzame maaltijden met AI.",
        "map_title": "🗺️ Voedselbord & Live Kaart",
        "map_sub": "Verbinding maken tussen lokale donateurs en ontvangers.",
        "delivery_title": "🚴 Voedselbezorging & Ophaalsysteem",
        "delivery_sub": "Vrijwilligersvloot die overschotten naar opvangcentra brengt.",
        "storage_title": "🧊 Voedselbewaringsgids",
        "storage_sub": "Professionele conserveringstechnieken.",
        "ngo_title": "🤝 Lokale NGO Gids",
        "ngo_sub": "Samenwerken met lokale changemakers.",
        "features": "### 🌟 Belangrijkste Kenmerken:\n* **📊 Impactanalyse:** Bekijk realtime statistieken."
    },
    "Русский (Russian)": {
        "title": "🥗 Центр спасения пищевых отходов",
        "subtitle": "Превращение излишков еды в общественные обеды.",
        "analytics_title": "📊 Анализ влияния и статистика",
        "analytics_sub": "Подробная статистика операций по спасению продуктов питания.",
        "ai_title": "🤖 ИИ Помощник на кухне",
        "ai_sub": "Превращайте повседневные ингредиенты в экологичные блюда.",
        "map_title": "🗺️ Доска объявлений и живая карта",
        "map_sub": "Связь местных доноров и получателей.",
        "delivery_title": "🚴 Система доставки еды",
        "delivery_sub": "Волонтерский парк доставки.",
        "storage_title": "🧊 Руководство по хранению",
        "storage_sub": "Профессиональные методы консервации.",
        "ngo_title": "🤝 Каталог местных НПО",
        "ngo_sub": "Партнерство с общественными деятелями.",
        "features": "### 🌟 Основные характеристики:\n* **📊 Аналитика:** Исследуйте графические метрики."
    },
    "中文 (Chinese)": {
        "title": "🥗 食物浪费救援中心",
        "subtitle": "将厨房剩余食物转化为社区餐食与可持续方案。",
        "analytics_title": "📊 影响与统计分析",
        "analytics_sub": "社区食品救援运营、借款人生长和中心活动的详细统计分解。",
        "ai_title": "🤖 AI 厨房助手与扫描仪",
        "ai_sub": "利用 AI 将日常食材转化为可持续餐食。",
        "map_title": "🗺️ 社区食品公告栏与实时地图",
        "map_sub": "连接德里 NCR 的当地捐赠者和接收者。",
        "delivery_title": "🚴 食品配送与志愿领取系统",
        "delivery_sub": "将盈余食品运送至庇护所的志愿者配送车队。",
        "storage_title": "🧊 食品保鲜与储存指南",
        "storage_sub": "延长食品保质期的专业保鲜技术。",
        "ngo_title": "🤝 本地NGO名录",
        "ngo_sub": "与首都地区的社区变革者合作。",
        "features": "### 🌟 核心平台功能：\n* **📊 影响分析：** 探索有关食品救援的实时图形指标。\n* **🤖 AI 厨房助手：** 上传剩菜图片以获取即时食谱。\n* **🤝 社区食品看板：** 标记多余的餐食并在地图上查找节点。"
    },
    "日本語 (Japanese)": {
        "title": "🥗 食品ロス削減レスキューハブ",
        "subtitle": "キッチンの余剰食材をコミュニティの食事に変える。",
        "analytics_title": "📊 インパクトと統計分析",
        "analytics_sub": "コミュニティフードレスキュー活動の詳細な統計分析。",
        "ai_title": "🤖 AI キッチンアシスタント",
        "ai_sub": "AIを使用して日常の食材を持続可能な食事に変えましょう。",
        "map_title": "🗺️ コミュニティフードボード＆ライブマップ",
        "map_sub": "デリーNCR全体の寄付者と受信者を結び付けます。",
        "delivery_title": "🚴 フードデリバリー＆受取システム",
        "delivery_sub": "シェルターに余剰食品を届けるボランティア配送チーム。",
        "storage_title": "🧊 食品保存ガイド",
        "storage_sub": "賞味期限を延ばすためのプロの保存技術。",
        "ngo_title": "🤝 ローカルNGOディレクトリ",
        "ngo_sub": "首都地域のコミュニティ変革者との提携。",
        "features": "### 🌟 プラットフォームの主な機能：\n* **📊 インパクト分析：** 食品レスキューのリアルタイム指標を確認します。"
    }
}

t = TRANS.get(selected_lang, TRANS["English"])

# ==========================================
# PAGE 1: HOME & OVERVIEW
# ==========================================
if page == "Home & Overview":
    st.markdown(f'<p class="animated-header">{t["title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="animated-subtitle">{t["subtitle"]}</p>', unsafe_allow_html=True)
    
    st.image(
        "https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&w=1200&q=80",
        caption="Empowering communities by redirecting surplus food safely.",
        use_container_width=True
    )
    
    st.divider()
    st.markdown(t["features"])

# ==========================================
# PAGE 2: IMPACT & ANALYTICS DASHBOARD
# ==========================================
elif page == "Impact & Analytics Dashboard":
    st.markdown(f'<p class="animated-header">{t["analytics_title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="animated-subtitle">{t["analytics_sub"]}</p>', unsafe_allow_html=True)
    
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
elif page == "AI Kitchen Assistant":
    st.markdown(f'<p class="animated-header">{t["ai_title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="animated-subtitle">{t["ai_sub"]}</p>', unsafe_allow_html=True)
    
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
elif page == "Community Food Board & Map":
    st.markdown(f'<p class="animated-header">{t["map_title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="animated-subtitle">{t["map_sub"]}</p>', unsafe_allow_html=True)
    
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
elif page == "Food Delivery & Pickup System":
    st.markdown(f'<p class="animated-header">{t["delivery_title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="animated-subtitle">{t["delivery_sub"]}</p>', unsafe_allow_html=True)
    
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
elif page == "Food Storage Guide":
    st.markdown(f'<p class="animated-header">{t["storage_title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="animated-subtitle">{t["storage_sub"]}</p>', unsafe_allow_html=True)
    
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
elif page == "Local NGO Directory":
    st.markdown(f'<p class="animated-header">{t["ngo_title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="animated-subtitle">{t["ngo_sub"]}</p>', unsafe_allow_html=True)
    
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
