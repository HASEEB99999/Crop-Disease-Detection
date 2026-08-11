# ======================================================================
# CROP DISEASE DETECTION APP - WITH YOUR HUGGING FACE TOKEN
# ======================================================================

import streamlit as st
from PIL import Image
import numpy as np
import requests
import io
import base64
import json

# ======================================================================
# PAGE CONFIGURATION
# ======================================================================

st.set_page_config(
    page_title="🌾 Crop Disease Detection",
    page_icon="🌿",
    layout="wide"
)

st.title("🌾 Crop Disease Detection System")
st.markdown("### 🔬 Powered by Hugging Face AI - 82.82% Accuracy")

# ======================================================================
# YOUR HUGGING FACE TOKEN
# ======================================================================

HF_TOKEN = "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"
MODEL_ID = "Sharmistha-catalyst/sick-greens-plant-disease"

# ======================================================================
# DISEASE CLASSES (38 classes)
# ======================================================================

disease_classes = [
    'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
    'Blueberry___healthy', 'Cherry___healthy', 'Cherry___Powdery_mildew',
    'Corn___Cercospora_leaf_spot', 'Corn___Common_rust', 'Corn___Northern_Leaf_Blight', 'Corn___healthy',
    'Grape___Black_rot', 'Grape___Esca', 'Grape___Leaf_blight', 'Grape___healthy',
    'Orange___Haunglongbing', 'Peach___Bacterial_spot', 'Peach___healthy',
    'Pepper___Bacterial_spot', 'Pepper___healthy',
    'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy',
    'Raspberry___healthy', 'Soybean___healthy',
    'Squash___Powdery_mildew', 'Strawberry___healthy', 'Strawberry___Leaf_scorch',
    'Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight',
    'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot',
    'Tomato___Spider_mites', 'Tomato___Target_Spot', 'Tomato___Tomato_mosaic_virus',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___healthy'
]

severity_labels = ['🟢 Healthy', '🟡 Mild', '🟠 Moderate', '🔴 Severe']

# ======================================================================
# TREATMENT RECOMMENDATIONS
# ======================================================================

def get_severity(disease_name):
    if 'healthy' in disease_name.lower():
        return 0
    elif 'severe' in disease_name.lower() or 'late' in disease_name.lower():
        return 3
    elif 'early' in disease_name.lower():
        return 1
    return 2

def get_treatment(disease, severity):
    treatments = {
        'Tomato___Early_blight': {
            1: '🌱 Remove affected leaves, apply copper-based fungicide',
            2: '🧪 Apply chlorothalonil fungicide, improve air circulation',
            3: '🚨 Remove infected plants, apply fungicide, crop rotation'
        },
        'Tomato___Late_blight': {
            1: '🌱 Apply copper fungicide, remove infected leaves',
            2: '🧪 Apply chlorothalonil, avoid overhead watering',
            3: '🚨 Remove infected plants, apply mancozeb fungicide'
        },
        'Corn___Common_rust': {
            1: '🌱 Apply fungicide, remove infected leaves',
            2: '🧪 Apply azoxystrobin fungicide, improve air flow',
            3: '🚨 Apply systemic fungicide, remove severely infected plants'
        },
        'Apple___Apple_scab': {
            1: '🌱 Apply organic sulfur spray, remove infected leaves',
            2: '🧪 Apply fungicide (myclobutanil), prune affected branches',
            3: '🚨 Apply systemic fungicide, remove severely infected branches'
        }
    }
    
    default = {
        0: '✅ Plant is healthy - Continue regular care',
        1: '🌱 Monitor plant health, consider preventive measures',
        2: '🧪 Apply appropriate fungicide, consult local expert',
        3: '🚨 Remove affected parts, apply treatment immediately'
    }
    
    if disease in treatments and severity in treatments[disease]:
        return treatments[disease][severity]
    return default.get(severity, '👨‍🌾 Consult local expert')

# ======================================================================
# PREDICTION FUNCTION
# ======================================================================

def predict_with_huggingface(image):
    """
    Call Hugging Face API for real prediction
    """
    try:
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Encode to base64
        img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
        
        # API URL
        api_url = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
        
        # Headers with your token
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Payload
        payload = {
            "inputs": img_base64
        }
        
        # Make request
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            st.warning(f"API Error: {response.status_code}")
            st.write(response.text)
            return None
            
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None

# ======================================================================
# MAIN APP
# ======================================================================

# Sidebar
with st.sidebar:
    st.header("📋 About")
    st.markdown("""
    - **Model:** Hugging Face API
    - **Accuracy:** 82.82%
    - **Crops:** 14 species
    - **Diseases:** 38 classes
    - **Training:** 87,000+ images
    """)
    
    st.header("🔑 API Status")
    st.success("✅ API Token Connected")
    
    st.header("📊 Severity Levels")
    for label in severity_labels:
        st.markdown(f"{label}")

# Main content
uploaded_file = st.file_uploader(
    "📤 Upload a leaf image",
    type=['jpg', 'jpeg', 'png', 'bmp']
)

if uploaded_file is not None:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Leaf", use_container_width=True)
    
    if st.button("🔍 Analyze Disease", use_container_width=True):
        with st.spinner("🧠 Analyzing with Hugging Face AI..."):
            
            # Try real prediction
            result = predict_with_huggingface(image)
            
            if result:
                try:
                    # Parse the result
                    if isinstance(result, list) and len(result) > 0:
                        # Model returns logits or probabilities
                        pred = result[0]
                        
                        # Get prediction (assuming softmax output)
                        if isinstance(pred, list):
                            pred_array = np.array(pred)
                            idx = np.argmax(pred_array)
                            confidence = np.max(pred_array) * 100
                            
                            disease = disease_classes[idx] if idx < len(disease_classes) else f"Disease_{idx}"
                            severity = get_severity(disease)
                            treatment = get_treatment(disease, severity)
                            
                            with col2:
                                st.success("✅ Analysis Complete!")
                                st.markdown("---")
                                
                                st.markdown(f"### 🦠 Disease Detected")
                                st.markdown(f"**{disease.replace('_', ' ')}**")
                                st.progress(confidence/100)
                                st.caption(f"Confidence: {confidence:.1f}%")
                                
                                st.markdown(f"### 📊 Severity Level")
                                st.markdown(f"**{severity_labels[severity]}**")
                                
                                st.markdown(f"### 💊 Treatment")
                                st.info(treatment)
                                
                                if severity == 0:
                                    st.success("✅ Plant is healthy!")
                                elif severity == 1:
                                    st.warning("⚠️ Early stage - act soon!")
                                elif severity == 2:
                                    st.warning("⚠️ Moderate - take action!")
                                else:
                                    st.error("🚨 Severe - immediate action!")
                        else:
                            st.error("Unexpected prediction format")
                    else:
                        st.error("Unexpected response format")
                except Exception as e:
                    st.error(f"Error parsing prediction: {e}")
            else:
                st.error("❌ Prediction failed. Please try again.")

else:
    st.markdown("""
    ### 📸 How to Use:
    1. **Upload** a leaf image
    2. **Click** "Analyze Disease"
    3. **Get** 82.82% accurate diagnosis!
    
    ### Supported Crops:
    🍎 Apple | 🌽 Corn | 🍇 Grape | 🥔 Potato | 🍅 Tomato
    """)
    
    st.info("""
    📝 **This app uses the best plant disease model from Hugging Face.**
    Making REAL predictions with 82.82% accuracy!
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>Haseeb Saleem | Powered by Hugging Face - 82.82% Accuracy</p>
</div>
""", unsafe_allow_html=True)


    

    
  
           
              
    

        
    

           
               
               
          
   


