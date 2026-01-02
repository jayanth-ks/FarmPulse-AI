from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_swagger_ui import get_swaggerui_blueprint
import json
import os
import base64
from io import BytesIO
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
import secrets
from supabase import create_client, Client
import firebase_admin
from firebase_admin import credentials, db

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))

# Initialize Groq client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

# Initialize Firebase Admin
try:
    firebase_creds_path = os.environ.get("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    if os.path.exists(firebase_creds_path):
        cred = credentials.Certificate(firebase_creds_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.environ.get("FIREBASE_DATABASE_URL")
        })
        print("Firebase initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize Firebase - {e}")


# In-memory storage for scan history
scan_history = []

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "FarmPulse AI - Plant Disease Detection API"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get sensor data from Firebase
    sensor_data = {
        'soil_moisture': 31,
        'temperature': 25.5,
        'humidity': 61,
        'pump_status': False,
        'pump_mode': 'AUTO'
    }
    
    try:
        if firebase_admin._apps:
            ref = db.reference('FarmPulse')
            data = ref.get()
            if data:
                sensor_data = {
                    'soil_moisture': data.get('soil', 73),
                    'temperature': data.get('temp', 27.3),
                    'humidity': data.get('hum', 71),
                    'pump_status': data.get('pump', False),
                    'pump_mode': 'AUTO' if data.get('read') else 'MANUAL'
                }
    except Exception as e:
        print(f"Error fetching Firebase data: {e}")
    
    return render_template('dashboard.html', sensor_data=sensor_data)

@app.route('/scan')
def scan():
    """Scan page"""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('scan.html')

@app.route('/history')
def history():
    """History page"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get history from Supabase
    history_data = []
    try:
        if supabase:
            user_id = session.get('user_id', session.get('user'))
            response = supabase.table('scan_history').select('*').eq('user_id', user_id).order('timestamp', desc=True).execute()
            history_data = response.data if response.data else []
    except Exception as e:
        print(f"Error fetching history from Supabase: {e}")
        history_data = scan_history
    
    return render_template('history.html', history=history_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email and password:
            session['user'] = email
            session['user_id'] = email
            return redirect(url_for('dashboard'))
    
    # Pass Google client ID (if set) so the template can initialize Google Identity
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    return render_template('login.html', google_client_id=google_client_id)

@app.route('/logout')
def logout():
    """Logout"""
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/predict', methods=['POST'])

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read and encode image to base64
        image = Image.open(file.stream).convert('RGB')
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Create the system prompt
        system_prompt = """You are an expert plant pathologist AI assistant. Analyze the provided plant image and identify any diseases present.

Your response must follow this exact structure:

If a disease is detected:
{
  "disease_detected": true,
  "disease_name": "Name of the disease",
  "confidence": 85,
  "crop_type": "Type of crop/plant",
  "probable_cause": "Brief explanation of what causes this disease",
  "description": "Detailed description of the disease symptoms and characteristics",
  "solution": "Comprehensive treatment and prevention measures",
  "severity": "Low/Medium/High"
}

If the plant is healthy:
{
  "disease_detected": false,
  "confidence": 95,
  "crop_type": "Type of crop/plant",
  "message": "Congratulations! Your crop appears to be healthy with no visible signs of disease. The leaves show good color, proper structure, and no spots or discoloration. Keep up the good agricultural practices!",
  "severity": "None"
}

Important guidelines:
- Express confidence as a percentage (0-100)
- Be specific and detailed in your analysis
- Provide actionable solutions
- Use professional agricultural terminology
- Only respond with valid JSON format"""

        # Make API call to Groq with vision model
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": system_prompt + "\n\nPlease analyze this plant image and identify any diseases."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.3,
            max_tokens=1024
        )
        
        # Extract and parse the response
        analysis_text = chat_completion.choices[0].message.content
        
        # Try to parse JSON from response
        try:
            # Remove markdown code blocks if present
            if '```json' in analysis_text:
                analysis_text = analysis_text.split('```json')[1].split('```')[0].strip()
            elif '```' in analysis_text:
                analysis_text = analysis_text.split('```')[1].split('```')[0].strip()
            
            analysis_result = json.loads(analysis_text)
            analysis_result['timestamp'] = datetime.now().isoformat()
            
            # Save to Supabase
            try:
                if supabase and 'user_id' in session:
                    scan_record = {
                        'user_id': session.get('user_id'),
                        'scan_type': 'groq',
                        'disease_detected': analysis_result.get('disease_detected'),
                        'disease_name': analysis_result.get('disease_name'),
                        'confidence': analysis_result.get('confidence'),
                        'crop_type': analysis_result.get('crop_type'),
                        'probable_cause': analysis_result.get('probable_cause'),
                        'description': analysis_result.get('description'),
                        'solution': analysis_result.get('solution'),
                        'severity': analysis_result.get('severity'),
                        'timestamp': datetime.now().isoformat()
                    }
                    supabase.table('scan_history').insert(scan_record).execute()
            except Exception as db_error:
                print(f"Error saving to Supabase: {db_error}")
            
            # Add to history
            scan_history.append({
                'type': 'groq',
                'result': analysis_result,
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            # If parsing fails, return raw text
            analysis_result = {
                "raw_response": analysis_text,
                "error": "Failed to parse JSON response",
                "timestamp": datetime.now().isoformat()
            }
        
        return jsonify(analysis_result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/signup', methods=['POST'])
def auth_signup():
    """Signup with Supabase"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        response = supabase.auth.sign_up({'email': email, 'password': password})
        
        # Check if user was created
        user = getattr(response, 'user', None)
        if user:
            session['user'] = email
            session['user_id'] = user.id if hasattr(user, 'id') else email
            # Session might be None for unconfirmed signups
            session_obj = getattr(response, 'session', None)
            if session_obj and hasattr(session_obj, 'access_token'):
                session['access_token'] = session_obj.access_token
            return jsonify({'success': True, 'user': email, 'message': 'Account created successfully'})
        else:
            return jsonify({'error': 'Signup failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Login with Supabase"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        response = supabase.auth.sign_in_with_password({'email': email, 'password': password})
        
        user = getattr(response, 'user', None)
        if user:
            session['user'] = email
            session['user_id'] = user.id if hasattr(user, 'id') else email
            session_obj = getattr(response, 'session', None)
            if session_obj and hasattr(session_obj, 'access_token'):
                session['access_token'] = session_obj.access_token
            return jsonify({'success': True, 'user': email})
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/google', methods=['POST'])
def auth_google():
    """Google OAuth login"""
    try:
        data = request.get_json()
        id_token = data.get('id_token')
        
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        response = supabase.auth.sign_in_with_id_token({'provider': 'google', 'token': id_token})
        
        user = getattr(response, 'user', None)
        if user:
            email = user.email if hasattr(user, 'email') else 'google_user'
            session['user'] = email
            session['user_id'] = user.id if hasattr(user, 'id') else email
            session_obj = getattr(response, 'session', None)
            if session_obj and hasattr(session_obj, 'access_token'):
                session['access_token'] = session_obj.access_token
            return jsonify({'success': True, 'user': email})
        else:
            return jsonify({'error': 'Google authentication failed'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/phone', methods=['POST'])
def auth_phone():
    """Phone OTP authentication"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        # Request OTP from Supabase and return diagnostic info to client
        response = supabase.auth.sign_in_with_otp({'phone': phone})
        # Return a simple diagnostic response so the frontend can show any Supabase message
        try:
            resp_data = response.data if hasattr(response, 'data') else str(response)
        except Exception:
            resp_data = str(response)
        return jsonify({'success': True, 'detail': resp_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    """Verify phone OTP"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        token = data.get('token')
        
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        response = supabase.auth.verify_otp({'phone': phone, 'token': token, 'type': 'sms'})
        try:
            # If Supabase returned a user/session, set session
            user = getattr(response, 'user', None)
            session_obj = getattr(response, 'session', None)
            if user:
                session['user'] = phone
                session['user_id'] = user.id if hasattr(user, 'id') else phone
                if session_obj and hasattr(session_obj, 'access_token'):
                    session['access_token'] = session_obj.access_token
                return jsonify({'success': True, 'user': phone})
        except Exception:
            pass

        # Fallback: return Supabase response details for debugging
        try:
            resp_data = response.data if hasattr(response, 'data') else str(response)
        except Exception:
            resp_data = str(response)
        return jsonify({'success': False, 'detail': resp_data}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor-data', methods=['GET'])
def get_sensor_data():
    """Get real-time sensor data from Firebase"""
    try:
        if firebase_admin._apps:
            ref = db.reference('FarmPulse')
            data = ref.get()
            if data:
                return jsonify({
                    'success': True,
                    'data': {
                        'soil_moisture': data.get('soil', 0),
                        'temperature': data.get('temp', 0),
                        'humidity': data.get('hum', 0),
                        'pump_status': data.get('pump', False),
                        'read': data.get('read', True),
                        'write': data.get('write', True)
                    }
                })
        return jsonify({'error': 'Firebase not configured'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pump-control', methods=['POST'])
def pump_control():
    """Control pump via Firebase"""
    try:
        data = request.get_json()
        pump_status = data.get('pump_status')
        
        if firebase_admin._apps:
            ref = db.reference('FarmPulse')
            ref.update({'pump': pump_status, 'write': True})
            return jsonify({'success': True, 'pump_status': pump_status})
        
        return jsonify({'error': 'Firebase not configured'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'groq_configured': os.environ.get("GROQ_API_KEY") is not None,
        'supabase_configured': supabase is not None,
        'firebase_configured': len(firebase_admin._apps) > 0,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
