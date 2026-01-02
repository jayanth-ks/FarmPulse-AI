# FarmPulse AI Setup Guide

## Prerequisites
- Python 3.9.6 or higher
- Supabase account
- Firebase project with Realtime Database
- Groq API key

## Installation Steps

### 1. Install Dependencies
```bash
cd farmpulse-app
pip install -r requirements.txt
```

### 2. Configure Supabase

1. Create a Supabase project at https://supabase.com
2. Go to Project Settings > API
3. Copy your project URL and anon/service keys
4. Update `.env` file:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

5. Run the SQL query to create the `scan_history` table:
```sql
CREATE TABLE scan_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    scan_type VARCHAR(20) NOT NULL CHECK (scan_type IN ('model', 'groq', 'sensor')),
    
    disease_detected BOOLEAN DEFAULT NULL,
    disease_name VARCHAR(255) DEFAULT NULL,
    confidence DECIMAL(5, 2) DEFAULT NULL,
    crop_type VARCHAR(255) DEFAULT NULL,
    probable_cause TEXT DEFAULT NULL,
    description TEXT DEFAULT NULL,
    solution TEXT DEFAULT NULL,
    severity VARCHAR(10) DEFAULT NULL CHECK (severity IN ('None', 'Low', 'Medium', 'High')),
    
    prediction VARCHAR(255) DEFAULT NULL,
    top_predictions JSONB DEFAULT NULL,
    
    soil_moisture DECIMAL(5, 2) DEFAULT NULL,
    temperature DECIMAL(5, 2) DEFAULT NULL,
    humidity DECIMAL(5, 2) DEFAULT NULL,
    pump_status VARCHAR(3) DEFAULT NULL CHECK (pump_status IN ('ON', 'OFF')),
    pump_mode VARCHAR(10) DEFAULT NULL CHECK (pump_mode IN ('AUTO', 'MANUAL')),
    
    image_path VARCHAR(500) DEFAULT NULL,
    image_data BYTEA DEFAULT NULL,
    
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_id ON scan_history(user_id);
CREATE INDEX idx_timestamp ON scan_history(timestamp);
CREATE INDEX idx_scan_type ON scan_history(scan_type);
```

6. Enable authentication providers in Supabase:
   - Go to Authentication > Providers
   - Enable Email provider
   - Enable Google OAuth (configure with Google Cloud Console)
   - Enable Phone (SMS) provider (configure with Twilio or similar)

### 3. Configure Firebase

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Realtime Database
3. Set database rules to allow authenticated read/write
4. Download service account credentials:
   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save as `firebase-credentials.json` in the project root

5. Update `.env` file:
```env
FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.asia-southeast1.firebasedatabase.app
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

6. Ensure your Firebase structure matches:
```json
{
  "FarmPulse": {
    "hum": 71,
    "pump": false,
    "soil": 73,
    "temp": 27.3,
    "read": true,
    "write": true
  }
}
```

### 4. ESP32 Configuration

Your ESP32 should push sensor data to Firebase in the following format:
```cpp
// Firebase paths
firebase.setFloat("FarmPulse/soil", soilMoisture);
firebase.setFloat("FarmPulse/temp", temperature);
firebase.setFloat("FarmPulse/hum", humidity);
firebase.setBool("FarmPulse/pump", pumpStatus);
firebase.setBool("FarmPulse/read", true);
```

### 5. Run the Application

```bash
python app.py
```

Access the application at: http://localhost:5000

## Features

### Authentication
- **Email/Password**: Standard email authentication via Supabase
- **Google OAuth**: One-click Google sign-in
- **Phone OTP**: SMS-based authentication

### Dashboard
- Real-time sensor data from Firebase (soil moisture, temperature, humidity)
- Pump status and control
- Auto/Manual mode switching

### Disease Detection
- AI-powered analysis using Groq Vision API
- Detailed disease information with treatment recommendations
- Results saved to Supabase database

### History
- View past disease detection scans
- Filter by date and result type
- Export scan history

## API Endpoints

- `POST /api/auth/login` - Email/password login
- `POST /api/auth/signup` - Create new account
- `POST /api/auth/google` - Google OAuth login
- `POST /api/auth/phone` - Send OTP to phone
- `POST /api/auth/verify-otp` - Verify phone OTP
- `GET /api/sensor-data` - Get current sensor readings
- `POST /api/pump-control` - Control pump on/off
- `POST /api/analyze` - Analyze plant image with AI
- `GET /api/health` - Health check endpoint

## Troubleshooting

### Firebase connection issues
- Verify credentials file path
- Check database URL format
- Ensure database rules allow access

### Supabase authentication fails
- Verify API keys are correct
- Check authentication providers are enabled
- Ensure email/phone provider is configured

### Sensor data not updating
- Check ESP32 is connected to Firebase
- Verify Firebase database structure
- Check console for Firebase errors

## Production Deployment

Before deploying to production:

1. Change `SECRET_KEY` in `.env`
2. Set `FLASK_DEBUG=False`
3. Use production WSGI server (gunicorn, waitress)
4. Set up SSL certificates
5. Configure CORS for frontend domains
6. Set up monitoring and logging
7. Implement rate limiting
8. Add data validation and sanitization
