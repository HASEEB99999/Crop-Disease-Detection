# ======================================================================
# CROP DISEASE DETECTION APP - WITH WORKING MODEL
# ======================================================================

import streamlit as st
from PIL import Image
import numpy as np
import tensorflow as tf
import json
from tensorflow.keras import backend as K

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
# LOAD MODEL
# ======================================================================

@st.cache_resource
def load_model():
    """Load the trained model"""
    try:
        # Define custom loss for loading
        def combined_loss():
            def loss(y_true, y_pred):
                return K.constant(0.0)
            return loss
        
        custom_objects = {'loss': combined_loss()}
        
        model = tf.keras.models.load_model(
            'efficientnetb0_best.h5',
            custom_objects=custom_objects,
            compile=False
        )
        return model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

# ======================================================================
# LOAD METADATA
# ======================================================================

@st.cache_resource
def load_metadata():
    try:
        with open('model_metadata.json') as f:
            return json.load(f)
    except:
        return None

# ======================================================================
# DISEASE CLASSES
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
# PREPROCESS FUNCTION
# ======================================================================

def preprocess_image(image):
    image = image.resize((224, 224))
    img_array = np.array(image)
    if len(img_array.shape) == 2:
        img_array = np.stack([img_array, img_array, img_array], axis=2)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def predict_disease(image, model, metadata=None):
    processed = preprocess_image(image)
    predictions = model.predict(processed, verbose=0)
    
    # Model has 3 outputs: disease, stage, days
    disease_pred = predictions[0]
    stage_pred = predictions[1] if len(predictions) > 1 else None
    days_pred = predictions[2] if len(predictions) > 2 else None
    
    disease_idx = np.argmax(disease_pred[0])
    confidence = np.max(disease_pred[0]) * 100
    
    disease_name = disease_classes[disease_idx]
    
    result = {
        'disease': disease_name,
        'confidence': confidence,
        'severity': get_severity(disease_name)
    }
    
    if stage_pred is not None:
        stage_idx = np.argmax(stage_pred[0])
        result['stage'] = ['Healthy', 'Early', 'Mid', 'Late'][stage_idx]
        result['stage_idx'] = stage_idx
    
    if days_pred is not None:
        result['days_infected'] = float(days_pred[0][0])
    
    return result

# ======================================================================
# MAIN APP
# ======================================================================

with st.sidebar:
    st.header("📋 About")
    st.markdown("""
    - **Model:** EfficientNetB0 (Trained)
    - **Accuracy:** 82.82%
    - **Crops:** 14 species
    - **Diseases:** 38 classes
    - **Training:** 87,000+ images
    """)
    
    st.header("📊 Severity Levels")
    for label in severity_labels:
        st.markdown(f"{label}")
    
    st.header("💡 Instructions")
    st.markdown("""
    1. Upload a leaf image
    2. Click 'Analyze Disease'
    3. Get AI diagnosis!
    """)

# Load model
with st.spinner("🔄 Loading AI Model..."):
    model = load_model()
    
    if model is None:
        st.error("❌ Could not load model. Please check the model file.")
        st.stop()
    
    st.success("✅ Model loaded successfully!")

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
        with st.spinner("🧠 Analyzing..."):
            result = predict_disease(image, model)
            
            if result:
                treatment = get_treatment(result['disease'], result['severity'])
                
                with col2:
                    st.success("✅ Analysis Complete!")
                    st.markdown("---")
                    
                    st.markdown(f"### 🦠 Disease Detected")
                    st.markdown(f"**{result['disease'].replace('_', ' ')}**")
                    st.progress(result['confidence']/100)
                    st.caption(f"Confidence: {result['confidence']:.1f}%")
                    
                    st.markdown(f"### 📊 Severity Level")
                    st.markdown(f"**{severity_labels[result['severity']]}**")
                    
                    if 'stage' in result:
                        st.markdown(f"### 📈 Disease Stage")
                        st.markdown(f"**{result['stage']}**")
                    
                    if 'days_infected' in result:
                        st.caption(f"Estimated days infected: ~{result['days_infected']:.1f} days")
                    
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

else:
    st.markdown("""
    ### 📸 How to Use:
    1. **Upload** a leaf image
    2. **Click** "Analyze Disease"
    3. **Get** AI diagnosis!
    
    ### Supported Crops:
    🍎 Apple | 🌽 Corn | 🍇 Grape | 🥔 Potato | 🍅 Tomato
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>Haseeb Saleem | EfficientNetB0 - 82.82% Accuracy</p>
</div>
""", unsafe_allow_html=True)


       
        

    


    

    
  
           
              
    

        
    

           
               
               
          
   


