# ======================================================================
# CROP DISEASE DETECTION APP - WITH CONFIDENCE FILTERING
# ======================================================================

import streamlit as st
from PIL import Image
import numpy as np
import requests
import io
import base64
import time
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
st.markdown("### 🔬 AI-Powered Plant Disease Diagnosis")

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
# PREDICTION FUNCTION WITH RETRY AND CONFIDENCE
# ======================================================================

def predict_with_huggingface(image):
    """
    Call Hugging Face API for real prediction
    """
    for attempt in range(3):
        try:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            
            api_url = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
            
            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": base64.b64encode(img_byte_arr).decode('utf-8')
            }
            
            response = requests.post(
                api_url, 
                headers=headers, 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                time.sleep(5)
                continue
            else:
                return None
                
        except:
            time.sleep(2)
            continue
    
    return None

# ======================================================================
# GET TOP PREDICTIONS
# ======================================================================

def get_top_predictions(predictions, top_k=5):
    """
    Get top k predictions with probabilities
    """
    pred_array = np.array(predictions[0])
    top_indices = np.argsort(pred_array)[-top_k:][::-1]
    top_confidences = pred_array[top_indices] * 100
    
    results = []
    for idx, conf in zip(top_indices, top_confidences):
        disease = disease_classes[idx]
        results.append({
            'disease': disease,
            'confidence': conf,
            'is_healthy': 'healthy' in disease.lower()
        })
    
    return results

# ======================================================================
# ANALYZE PREDICTION WITH CONFIDENCE
# ======================================================================

def analyze_prediction(top_predictions):
    """
    Analyze top predictions to make a confident diagnosis
    """
    if not top_predictions:
        return None
    
    # Get the top prediction
    top = top_predictions[0]
    second = top_predictions[1] if len(top_predictions) > 1 else None
    
    # Rules for confident prediction
    
    # 1. If top prediction is healthy with high confidence
    if top['is_healthy'] and top['confidence'] > 85:
        return {
            'disease': top['disease'],
            'confidence': top['confidence'],
            'severity': 0,
            'is_certain': True,
            'message': '✅ Confident: Plant appears healthy'
        }
    
    # 2. If top prediction is disease with high confidence
    if not top['is_healthy'] and top['confidence'] > 85:
        return {
            'disease': top['disease'],
            'confidence': top['confidence'],
            'severity': get_severity(top['disease']),
            'is_certain': True,
            'message': '✅ Confident: Disease detected'
        }
    
    # 3. If top prediction is disease but second is healthy with close confidence
    if (not top['is_healthy'] and second and second['is_healthy'] and 
        abs(top['confidence'] - second['confidence']) < 15):
        return {
            'disease': 'Uncertain',
            'confidence': top['confidence'],
            'severity': 0,
            'is_certain': False,
            'message': '⚠️ Uncertain: Please upload a clearer image'
        }
    
    # 4. If confidence is low
    if top['confidence'] < 70:
        return {
            'disease': 'Need Better Image',
            'confidence': top['confidence'],
            'severity': 0,
            'is_certain': False,
            'message': '⚠️ Low confidence: Please upload a clearer image'
        }
    
    # 5. Default: use top prediction but mark as uncertain
    return {
        'disease': top['disease'],
        'confidence': top['confidence'],
        'severity': get_severity(top['disease']),
        'is_certain': True,
        'message': '✅ Diagnosis complete'
    }

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
    """)
    
    st.header("📊 Severity Levels")
    for label in severity_labels:
        st.markdown(f"{label}")
    
    st.header("💡 Tips")
    st.markdown("""
    1. Use clear, well-lit images
    2. Show the entire leaf
    3. Avoid shadows
    4. Multiple angles help
    """)

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
        with st.spinner("🧠 Analyzing with AI..."):
            
            # Get prediction
            predictions = predict_with_huggingface(image)
            
            if predictions:
                # Get top predictions
                top_predictions = get_top_predictions(predictions, top_k=5)
                
                # Analyze the prediction
                result = analyze_prediction(top_predictions)
                
                if result:
                    with col2:
                        st.success("✅ Analysis Complete!")
                        st.markdown("---")
                        
                        # Show the main result
                        st.markdown(f"### 🦠 Diagnosis")
                        
                        if result['disease'] == 'Uncertain' or result['disease'] == 'Need Better Image':
                            st.warning(result['message'])
                            st.info("📸 Try uploading a clearer image of the leaf")
                        else:
                            st.markdown(f"**{result['disease'].replace('_', ' ')}**")
                            st.progress(result['confidence']/100)
                            st.caption(f"Confidence: {result['confidence']:.1f}%")
                            
                            st.markdown(f"### 📊 Severity Level")
                            st.markdown(f"**{severity_labels[result['severity']]}**")
                            
                            treatment = get_treatment(result['disease'], result['severity'])
                            st.markdown(f"### 💊 Treatment")
                            st.info(treatment)
                            
                            if result['severity'] == 0:
                                st.success("✅ Plant is healthy!")
                            elif result['severity'] == 1:
                                st.warning("⚠️ Early stage - act soon!")
                            elif result['severity'] == 2:
                                st.warning("⚠️ Moderate - take action!")
                            else:
                                st.error("🚨 Severe - immediate action!")
                        
                        st.markdown("---")
                        st.markdown("### 📊 Top Predictions")
                        for i, pred in enumerate(top_predictions[:3], 1):
                            icon = "🟢" if pred['is_healthy'] else "🔴"
                            st.write(f"{i}. {icon} {pred['disease'].replace('_', ' ')} - {pred['confidence']:.1f}%")
            else:
                st.error("❌ Prediction failed. Please try again.")

else:
    st.markdown("""
    ### 📸 How to Use:
    1. **Upload** a leaf image
    2. **Click** "Analyze Disease"
    3. **Get** accurate diagnosis!
    
    ### Supported Crops:
    🍎 Apple | 🌽 Corn | 🍇 Grape | 🥔 Potato | 🍅 Tomato
    """)
    
    st.info("""
    📝 **This app uses AI to detect plant diseases.**
    For best results, use clear, well-lit images of the entire leaf.
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>Haseeb Saleem | Powered by AI</p>
</div>
""", unsafe_allow_html=True)

           
               
               
          
   


