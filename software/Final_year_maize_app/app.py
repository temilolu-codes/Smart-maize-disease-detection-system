from flask import Flask, render_template, request, jsonify, url_for, redirect
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from werkzeug.utils import secure_filename
import datetime
from tensorflow.keras.applications.efficientnet import preprocess_input  # CHANGED: EfficientNet preprocessing
import io
from PIL import Image
import requests


# ------------------------------------------------
# CONFIG
# ------------------------------------------------
UPLOAD_FOLDER = "static/uploads"
DEMO_FOLDER = "static/demo"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Define your 4 classes (make sure this matches your training order)
CLASS_LABELS = ["Blight", "Common Rust", "Gray Leaf Spot", "Healthy"]

# Enhanced disease info dictionary with comprehensive solutions
disease_info = {
    "Blight": {
        "info": "Northern Corn Leaf Blight is a fungal disease caused by Exserohilum turcicum. It appears as cigar-shaped lesions with dark borders on corn leaves, reducing photosynthetic area and potentially causing significant yield loss.",
        "symptoms": [
            "Long, elliptical gray-green to tan colored lesions",
            "Lesions may have dark borders",
            "Lesions typically 1-6 inches long",
            "May cause premature leaf death"
        ],
        "causes": [
            "High humidity (above 90%)",
            "Moderate temperatures (64-81°F)",
            "Poor air circulation",
            "Infected crop residue",
            "Susceptible corn varieties"
        ],
        "immediate_actions": [
            "Remove and destroy infected plant debris",
            "Improve air circulation around plants",
            "Avoid overhead irrigation if possible",
            "Apply fungicide if infection is severe"
        ],
        "treatments": [
            "Fungicides: Propiconazole, Azoxystrobin, or Pyraclostrobin",
            "Copper-based fungicides for organic treatment",
            "Apply treatments at first sign of disease",
            "Repeat applications every 7-14 days as needed"
        ],
        "prevention": [
            "Plant resistant varieties when available",
            "Practice crop rotation (avoid corn-after-corn)",
            "Manage crop residue properly",
            "Ensure proper plant spacing for air circulation",
            "Monitor weather conditions and apply preventive treatments"
        ],
        "solution": "Apply recommended fungicides immediately and improve field ventilation. Consider resistant varieties for next season."
    },
    
    "Common Rust": {
        "info": "Common rust is caused by the fungus Puccinia sorghi. It appears as small, reddish-brown pustules (uredinia) on both sides of corn leaves. While generally not as destructive as other diseases, it can reduce yield under favorable conditions.",
        "symptoms": [
            "Small, reddish-brown pustules on leaves",
            "Pustules on both upper and lower leaf surfaces",
            "Pustules may turn black later in season",
            "Yellow halo may surround pustules"
        ],
        "causes": [
            "Cool, moist weather conditions",
            "High humidity",
            "Temperatures between 60-77°F",
            "Poor air circulation",
            "Susceptible varieties"
        ],
        "immediate_actions": [
            "Monitor field regularly for early detection",
            "Remove severely infected leaves if practical",
            "Improve air circulation",
            "Consider fungicide application if spreading rapidly"
        ],
        "treatments": [
            "Fungicides: Tebuconazole, Propiconazole, or Azoxystrobin",
            "Triazole-based fungicides are most effective",
            "Apply when 5-10% of plants show symptoms",
            "Organic options: Copper fungicides, neem oil"
        ],
        "prevention": [
            "Plant resistant hybrids",
            "Ensure adequate plant spacing",
            "Avoid excessive nitrogen fertilization",
            "Practice crop rotation",
            "Remove alternate hosts (oxalis plants) if present"
        ],
        "solution": "Use resistant hybrids and apply fungicides when symptoms first appear. Monitor weather conditions closely."
    },
    
    "Gray Leaf Spot": {
        "info": "Gray Leaf Spot is caused by the fungus Cercospora zeae-maydis. It produces rectangular, gray to tan lesions with yellow halos on corn leaves. This disease thrives in warm, humid conditions and can cause significant yield loss.",
        "symptoms": [
            "Rectangular gray to tan lesions",
            "Lesions are parallel to leaf veins",
            "Yellow halo around lesions",
            "Lesions may merge to form large necrotic areas",
            "Premature leaf death in severe cases"
        ],
        "causes": [
            "High humidity (>90%)",
            "Warm temperatures (75-85°F)",
            "Extended leaf wetness",
            "Poor air circulation",
            "Continuous corn production",
            "Infected crop residue"
        ],
        "immediate_actions": [
            "Scout fields regularly during humid weather",
            "Remove infected plant debris",
            "Improve air circulation around plants",
            "Apply fungicide at early symptoms"
        ],
        "treatments": [
            "Fungicides: Azoxystrobin, Pyraclostrobin, or Propiconazole",
            "Strobilurin fungicides are highly effective",
            "Apply at tasseling stage or when symptoms first appear",
            "Tank mix with triazole fungicides for better control"
        ],
        "prevention": [
            "Use resistant or tolerant hybrids",
            "Practice minimum 2-year rotation away from corn",
            "Manage crop residue through tillage",
            "Ensure proper plant population and spacing",
            "Apply preventive fungicides in high-risk areas"
        ],
        "solution": "Apply strobilurin-based fungicides as needed and practice crop rotation to break disease cycle."
    },
    
    "Healthy": {
        "info": "The leaf appears healthy with no visible signs of disease. This indicates good plant health and proper management practices.",
        "symptoms": [
            "Green, vibrant leaf color",
            "No visible lesions or spots",
            "Normal leaf texture and structure",
            "No signs of chlorosis or necrosis"
        ],
        "causes": [
            "Proper nutrient management",
            "Adequate moisture levels",
            "Good air circulation",
            "Disease-resistant varieties",
            "Effective pest management"
        ],
        "immediate_actions": [
            "Continue current management practices",
            "Monitor regularly for any changes",
            "Maintain proper nutrition and irrigation",
            "Keep detailed records of successful practices"
        ],
        "treatments": [
            "No treatment required",
            "Continue preventive measures",
            "Monitor for early signs of any issues"
        ],
        "prevention": [
            "Continue current successful practices",
            "Regular field monitoring",
            "Maintain plant nutrition program",
            "Ensure proper irrigation management",
            "Keep detailed management records"
        ],
        "solution": "No action required. Maintain current good management practices and continue regular monitoring."
    }
}

# ------------------------------------------------
# INIT APP + LOAD MODEL
# ------------------------------------------------
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Load EfficientNet model
MODEL_PATH = "models/best_model.keras"

print(f"Loading EfficientNet model from: {MODEL_PATH}")
try:
    model = load_model(MODEL_PATH, compile=False, custom_objects=None)
    print("✅ AI model loaded successfully!")
    print(f"Model input shape: {model.input_shape}")
    print(f"Model output shape: {model.output_shape}")
except Exception as e:
    print(f"❌ Error loading model: {str(e)}")
    model = None

# ------------------------------------------------
# UTILS
# ------------------------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def predict_image(img_path):
    """Preprocess and detect a single image using EfficientNet preprocessing"""
    try:
        # Load and preprocess image
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        
        # Use EfficientNet preprocessing
        img_array = preprocess_input(img_array)
        
        # Predict
        preds = model.predict(img_array, verbose=0)[0]
        class_idx = np.argmax(preds)
        confidence = preds[class_idx]
        
        print(f"🔍 Detection probabilities: {dict(zip(CLASS_LABELS, preds))}")
        print(f"🎯 Detected: {CLASS_LABELS[class_idx]} with {confidence:.4f} confidence")
        
        return CLASS_LABELS[class_idx], float(confidence)
        
    except Exception as e:
        print(f"❌ Error in predict_image: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

def predict_image_from_bytes(img_bytes):
    """Preprocess and predict image from byte data (ESP32) using EfficientNet preprocessing"""
    try:
        # Open image from bytes
        img_data = io.BytesIO(img_bytes)
        img = Image.open(img_data)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to model input size
        img = img.resize((224, 224))
        
        # Convert to array and preprocess
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        
        # Use EfficientNet preprocessing
        img_array = preprocess_input(img_array)
        
        # Predict
        preds = model.predict(img_array, verbose=0)[0]
        class_idx = np.argmax(preds)
        confidence = preds[class_idx]
        
        print(f"🔍 ESP32 Prediction probabilities: {dict(zip(CLASS_LABELS, preds))}")
        print(f"🎯 ESP32 Predicted: {CLASS_LABELS[class_idx]} with {confidence:.4f} confidence")
        
        return CLASS_LABELS[class_idx], float(confidence)
        
    except Exception as e:
        print(f"❌ Error in predict_image_from_bytes: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

# Store prediction history
prediction_history = []

# ------------------------------------------------
# ROUTES
# ------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/trigger_esp32", methods=["POST"])
def trigger_esp32():
    """Trigger ESP32 camera to capture and upload an image"""
    try:
        # You'll need to update this IP to your ESP32's IP address
        esp32_ip = "192.168.98.105"  # Update this with your ESP32's actual IP
        esp32_url = f"http://{esp32_ip}/capture"
        
        response = requests.get(esp32_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "status": "success", 
                "message": "ESP32 camera triggered successfully!",
                "esp32_response": result
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"ESP32 returned error: {response.status_code}"
            }), 400
            
    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error", 
            "message": "Timeout: ESP32 didn't respond in time"
        }), 500
    except requests.exceptions.ConnectionError:
        return jsonify({
            "status": "error", 
            "message": "Cannot connect to ESP32. Check if it's online and IP is correct."
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error: {str(e)}"
        }), 500

@app.route("/upload", methods=["POST"])
def upload_file():
    if model is None:
        return jsonify({"error": "Model not loaded. Please check server logs."}), 500
        
    print(f"Received request - Content-Type: {request.content_type}")
    print(f"Request data length: {len(request.data) if request.data else 0}")
    
    # Handle ESP32 raw image data
    if request.data and len(request.data) > 0:
        try:
            print(f"Processing ESP32 image data... ({len(request.data)} bytes)")
            
            # Verify it's a JPEG image
            if len(request.data) < 2 or request.data[0] != 0xFF or request.data[1] != 0xD8:
                print("Warning: Data doesn't appear to be a JPEG image")
            else:
                print("✅ Valid JPEG image received from ESP32")
            
            # Predict from byte data
            label, confidence = predict_image_from_bytes(request.data)
            
            if label is None:
                return jsonify({"error": "Failed to process the image"}), 400
            
            # Save image for history and verification
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"esp32_capture_{timestamp}.jpg"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            
            # Create directory if it doesn't exist
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(request.data)
            
            print(f"✅ Image saved as: {filename}")
            print(f"💡 You can view it at: http://192.168.8.105:5000/static/uploads/{filename}")
            
            # Save to history
            prediction_history.append({
                "filename": filename,
                "label": label,
                "confidence": confidence,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "ESP32"
            })
            
            print(f"🏆 Model Prediction: {label} (confidence: {confidence:.2%})")
            # In your upload route, add this debug print:
            print(f"Saving to history: {prediction_history[-1]}")
            return jsonify({
                "status": "success",
                "label": label,
                "confidence": confidence,
                "info": disease_info[label]["info"],
                "solution": disease_info[label]["solution"],
                "saved_as": filename
            })
            
        except Exception as e:
            print(f"❌ Error processing ESP32 image: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Failed to process the image", "message": str(e)}), 400
    
    # Handle file upload from web interface
    elif "file" in request.files:
        file = request.files["file"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            label, confidence = predict_image(save_path)
            
            if label is None:
                return jsonify({"error": "Failed to process the image"}), 400

            # Save to history
            prediction_history.append({
                "filename": filename,
                "label": label,
                "confidence": confidence,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Web Upload"
            })

            # Check if request wants JSON response (AJAX) or page redirect
            # Replace this:
            # if request.headers.get('Content-Type') == 'application/json' or 'application/json' in request.headers.get('Accept', ''):

            # With this:
            accepts_json = 'application/json' in (request.headers.get('Accept', '') or '')
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            wants_json = accepts_json or is_ajax or request.args.get('ajax') == '1'

            if wants_json:
                return jsonify({
                    "status": "success",
                    "label": label,
                    "confidence": confidence,
                    "info": disease_info[label]["info"],
                    "solution": disease_info[label]["solution"],
                    "filename": filename
                })
            else:
                return redirect(f"/result/{filename}")

        else:
            return jsonify({"error": "Invalid file format"}), 400
    
    else:
        return jsonify({"error": "No file uploaded"}), 400

@app.route("/dashboard")
def dashboard():
    # Demo predictions – real model inference
    demo_files = ["healthy.jpg", "blight.jpg", "grayleaf.jpg", "rust.jpg"]
    demo_results = []
    for f in demo_files:
        path = os.path.join(DEMO_FOLDER, f)
        if os.path.exists(path):
            label, confidence = predict_image(path)
            if label is not None:
                demo_results.append({
                    "filename": f,
                    "label": label,
                    "confidence": round(confidence * 100, 2)  # Convert to percentage
                })

    # History predictions – ESP32 or manual uploads
    # Convert dict format to object-like format for template compatibility
    history = []
    for record in prediction_history[::-1]:  # Newest first
        history.append({
            "filename": record["filename"],
            "label": record["label"],
            "confidence": record["confidence"]
        })

    return render_template(
        "dashboard.html",
        demo_results=demo_results,
        history=history,
        disease_info=disease_info
    )

@app.route("/history")
def history():
    # Convert dict format to template-friendly format
    history_items = []
    for record in prediction_history[::-1]:  # Newest first
        history_items.append({
            "filename": record["filename"],
            "label": record["label"],
            "confidence": record["confidence"],
            "time": record["time"],
            "source": record.get("source", "Unknown")
        })
    
    return render_template("history.html", items=history_items)

@app.route("/result/<filename>")
def result(filename):
    """Show individual result page for a specific image"""
    # Find the prediction for this filename
    prediction = None
    for record in prediction_history:
        if record["filename"] == filename:
            prediction = record
            break
    
    if not prediction:
        return redirect("/dashboard")
    
    return render_template(
        "result.html",
        filename=filename,
        label=prediction["label"],
        confidence=prediction["confidence"],
        info=disease_info[prediction["label"]]["info"],
        solution=disease_info[prediction["label"]]["solution"],
        disease_info=disease_info,  # Pass the entire dictionary
        time=prediction["time"],
        source=prediction.get("source", "Unknown")
    )

# Health check endpoint
@app.route("/health")
def health():
    model_status = "loaded" if model is not None else "failed"
    return jsonify({
        "status": "healthy", 
        "model_status": model_status,
        "model_path": MODEL_PATH,
        "timestamp": datetime.datetime.now().isoformat()
    })

# Model info endpoint
@app.route("/model_info")
def model_info():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500
    
    return jsonify({
        "model_type": "EfficientNetB0",
        "input_shape": model.input_shape,
        "output_shape": model.output_shape,
        "classes": CLASS_LABELS,
        "num_classes": len(CLASS_LABELS)
    })

# ------------------------------------------------
# MAIN
# ------------------------------------------------
if __name__ == "__main__":
    # Create necessary directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DEMO_FOLDER, exist_ok=True)
    
    print("🚀 Starting Flask server with EfficientNet model...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Demo folder: {DEMO_FOLDER}")
    print(f"🤖 Model path: {MODEL_PATH}")
    print(f"📊 Classes: {CLASS_LABELS}")
    
    if model is not None:
        print("✅ Model loaded successfully! Ready to serve detections.")
    else:
        print("❌ Model failed to load. Check the model path and file.")
    
    app.run(debug=True, host="0.0.0.0", port=5000)