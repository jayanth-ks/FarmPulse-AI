# FarmPulse AI - Plant Disease Detection System

A comprehensive Flask-based web application for detecting plant diseases using AI-powered computer vision and machine learning models.

## 🌟 Features

- **Dual Detection Methods**
  - EfficientNet B3 Model: Fast, accurate predictions for 38+ plant diseases
  - Groq AI Vision: Detailed analysis with causes, descriptions, and treatment solutions

- **User-Friendly Interface**
  - Modern, responsive design with Tailwind CSS
  - Mobile-optimized with camera capture support
  - Dashboard with scan history and analytics
  - Real-time disease detection and analysis

- **API Documentation**
  - Interactive Swagger UI at `/api/docs`
  - RESTful API endpoints
  - Comprehensive OpenAPI 3.0 specification

- **Key Capabilities**
  - Multi-crop disease detection (Tomato, Apple, Corn, Grape, Potato, etc.)
  - Confidence scores and severity ratings
  - Treatment recommendations
  - Scan history tracking
  - Mobile camera integration

## 📋 Requirements

- Python 3.9+
- TensorFlow 2.13+
- Flask 2.3+
- Groq API key

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd farmpulse-app
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and update with your credentials:

```bash
copy .env.example .env  # Windows
# or
cp .env.example .env    # Linux/Mac
```

Edit `.env` file:
```env
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key-here
FLASK_ENV=development
FLASK_DEBUG=True
```

Get your Groq API key from: https://console.groq.com

### 5. Run the Application

```bash
python app.py
```

The application will be available at:
- Main app: `http://localhost:5000`
- API docs: `http://localhost:5000/api/docs`

## 📱 Usage

### Web Interface

1. **Landing Page** (`/`)
   - Overview of features and capabilities
   - Quick access to login and API documentation

2. **Login** (`/login`)
   - Demo credentials pre-filled for testing
   - Session-based authentication

3. **Dashboard** (`/dashboard`)
   - View statistics and recent scans
   - Quick actions for new scans
   - Scan history overview

4. **Scan Page** (`/scan`)
   - Upload images or use camera
   - Choose between Model Prediction or AI Analysis
   - View detailed results with recommendations

5. **History** (`/history`)
   - Complete scan history
   - Filter and review past analyses

### API Endpoints

#### Health Check
```bash
GET /api/health
```

#### Model Prediction
```bash
POST /api/predict
Content-Type: multipart/form-data
Body: file (image file)
```

#### AI Analysis
```bash
POST /api/analyze
Content-Type: multipart/form-data
Body: file (image file)
```

### Example API Usage

```python
import requests

# Model Prediction
with open('plant_image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/predict',
        files={'file': f}
    )
    print(response.json())

# AI Analysis
with open('plant_image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/analyze',
        files={'file': f}
    )
    print(response.json())
```

## 🏗️ Project Structure

```
farmpulse-app/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables
├── .env.example                   # Environment template
├── robots.txt                     # Crawler instructions
├── efficientnet_b3_crop_disease.h5  # ML model
├── label_map.json                 # Disease class mappings
├── static/
│   └── swagger.json              # OpenAPI specification
└── templates/
    ├── index.html                # Landing page
    ├── login.html                # Login page
    ├── dashboard.html            # Dashboard
    ├── scan.html                 # Scan interface
    └── history.html              # Scan history
```

## 🎨 Technology Stack

- **Backend**: Flask 2.3, Python 3.9+
- **ML/AI**: TensorFlow, Groq AI (Llama-4-Scout)
- **Frontend**: Tailwind CSS, Vanilla JavaScript
- **API Docs**: Swagger UI, OpenAPI 3.0
- **Model**: EfficientNet B3 (38 disease classes)

## 🔒 Security Features

- Session-based authentication
- robots.txt to disallow API endpoint crawling
- Environment variable management
- Input validation and error handling
- CSRF protection ready

## 📊 Supported Plant Diseases

The system can detect 38+ diseases across multiple crops including:
- **Tomato**: Early Blight, Late Blight, Leaf Mold, Septoria Leaf Spot, etc.
- **Apple**: Scab, Black Rot, Cedar Apple Rust
- **Corn**: Gray Leaf Spot, Common Rust, Northern Leaf Blight
- **Grape**: Black Rot, Esca, Leaf Blight
- **Potato**: Early Blight, Late Blight
- And many more...

## 🤝 Contributing

This is a demo application. For production use:
1. Implement proper user authentication
2. Add database for persistent storage
3. Set up proper session management
4. Add rate limiting and security headers
5. Use production WSGI server (Gunicorn, uWSGI)

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- EfficientNet model for disease classification
- Groq AI for advanced vision analysis
- Tailwind CSS for styling
- Flask community for excellent documentation

## 📧 Support

For issues or questions:
- Open an issue on GitHub
- Check API documentation at `/api/docs`
- Review the code and comments

---

Built with ❤️ for smarter farming
