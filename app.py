# ======================================================================
# IMPROVED PREDICTION WITH CONFIDENCE THRESHOLD
# ======================================================================

def predict_with_confidence(image, confidence_threshold=75):
    """
    Make prediction with confidence filtering
    """
    result = predict_disease(image)
    
    if result:
        # If confidence is low, mark as uncertain
        if result['confidence'] < confidence_threshold:
            return {
                'disease': 'Uncertain',
                'confidence': result['confidence'],
                'severity': 0,
                'is_certain': False
            }
        
        # If model predicts healthy but confidence is low, it might be wrong
        if 'healthy' in result['disease'].lower() and result['confidence'] < 85:
            return {
                'disease': 'Need Better Image',
                'confidence': result['confidence'],
                'severity': 0,
                'is_certain': False
            }
        
        # If model predicts disease with high confidence, likely correct
        if 'healthy' not in result['disease'].lower() and result['confidence'] > 80:
            return {
                'disease': result['disease'],
                'confidence': result['confidence'],
                'severity': get_severity(result['disease']),
                'is_certain': True
            }
    
    return result
  
 
       
        
  
   
     
