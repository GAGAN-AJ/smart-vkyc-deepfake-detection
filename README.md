# Smart-vKYC - AI-Powered vKYC with Deepfake and Liveness Detection

A full-stack video Know-Your-Customer (vKYC) platform that uses machine-learning models to verify a user's identity in real time during a live video call. The system combines document OCR, Aadhaar QR-code extraction, face matching, liveness detection, and deepfake detection to flag fraudulent verification attempts.

This was developed as a final-year engineering project and rebuilt from scratch as a personal portfolio project.


## Key Features

- Identity Document Verification - Upload an Aadhaar / PAN / Voter ID / Driving License / Passport; Tesseract OCR extracts the printed name and the system cross-checks it against the registered user record using fuzzy string matching (RapidFuzz).
- Aadhaar QR Code Extraction - OpenCV + zxing-cpp pipeline with multi-stage preprocessing (grayscale, upscaling, sharpening, Otsu thresholding) attempts to decode the embedded QR. When the QR is plain-XML (older Aadhaar format), structured fields (name, DOB, gender, pincode) are parsed via lxml; for the newer signed/encrypted Secure QR format, the system gracefully falls back to OCR-based name matching.
- Live Video Conferencing - Powered by the Agora RTC SDK, with screen share, mic/camera controls, and a one-click room creation flow.
- Real-time Deepfake Detection - A HuggingFace Vision Transformer (prithivMLmods/Deep-Fake-Detector-v2-Model) streams a per-second probability score during the call.
- Liveness Detection - dlib's 68-point facial landmark predictor computes Eye Aspect Ratio (EAR) to detect blinks and reject static photos or pre-recorded videos.
- Face Matching - DeepFace + FaceNet512 compares the uploaded document photo against the live video feed.
- Admin / Agent Dashboard - Verification officers see a live security panel during calls (Reality Integrity, ID Matching, Liveness gauge) and a full audit log of every session with pass/fail decisions and rejection reasons.
- Geo-IP Logging - Each verification session records the client's IP and approximate location.
- JWT Authentication - Bcrypt-hashed passwords, role-based access (Client / Admin), and a one-time admin secret for role escalation.


## Tech Stack

Backend
- Python 3.11, FastAPI, Uvicorn
- PostgreSQL with SQLAlchemy ORM
- PyTorch (deepfake), TensorFlow + DeepFace (face match), dlib (liveness)
- OpenCV, zxing-cpp, pytesseract, lxml, RapidFuzz, agora-token-builder
- WebSockets for real-time AI streaming

Frontend
- React 19 + Vite
- Material UI (MUI) + TailwindCSS
- Agora RTC SDK NG
- Framer Motion
- Axios

Infrastructure
- Git LFS (for the 95 MB dlib facial-landmark model)
- .env-based configuration with python-dotenv


## How the Verification Works

1. CLIENT REGISTERS
   Account stored (bcrypt-hashed password) in PostgreSQL.

2. DOCUMENT UPLOAD
   - File saved with a UUID-secured filename
   - QR-decode pipeline: OpenCV detectAndDecodeMulti, then preprocessed retries (grayscale, upscaling 1.5x-3x, sharpening, Otsu threshold), then zxing-cpp fallback
   - Tesseract OCR extracts printed text from the ID
   - Fuzzy match (RapidFuzz partial_ratio) between OCR text and the registered DB name produces a percentage match score
   - If score >= 70%, document is marked verified

3. LIVE VIDEO CALL
   - Agora room created with a backend-signed RTC token
   - Client publishes camera feed via Agora
   - Browser captures every 500 ms and streams JPEG frames over WebSocket to the FastAPI backend
   - Backend runs:
       Deepfake transformer on rolling 60-frame chunks
       dlib EAR-based liveness check
       FaceNet512 distance vs the uploaded document photo
   - Scores stored in verification_results table with IP, location, failure reason, and pass/fail decision

4. ADMIN DECISION
   Live AI dashboard during the call plus a persistent audit log table.


## Project Structure

```
SmartVkycProject/
  backend/
    main.py                          # FastAPI app + WebSocket pipeline
    app/
      auth/                          # JWT, password hashing, Agora tokens
      verification/
        deepfake.py                  # ViT-based deepfake detector
        liveness.py                  # dlib EAR liveness check
        face_match.py                # DeepFace FaceNet512 wrapper
        document_ocr.py              # Tesseract + OpenCV + zxing-cpp pipeline
        ml_models/                   # dlib landmark .dat (Git LFS)
    database/                        # SQLAlchemy models + DB session
    requirements.txt
  frontend/
    src/
      pages/                         # Login, Register, Dashboard,
                                     # DocumentVerification, VideoConference
      components/                    # Navbar, Sidebar, Layout
      context/AuthContext.jsx
    package.json
    vite.config.js
  README.md
```


## Setup Instructions

Prerequisites
- Python 3.11 (Anaconda / Miniconda recommended)
- Node.js 18+
- PostgreSQL 14+
- Tesseract OCR (default install path on Windows: C:\Program Files\Tesseract-OCR\)
- Git LFS (required to fetch the dlib facial-landmark model)
- An Agora free-tier project (App ID + App Certificate, Secured-mode tokens)

1. Clone the repository

```
git clone https://github.com/GAGAN-AJ/smart-vkyc-deepfake-detection.git
cd smart-vkyc-deepfake-detection
git lfs pull
```

2. PostgreSQL

Create a database named vkycdb and note the connection string.

3. Backend

```
conda create -n vkyc python=3.11 -y
conda activate vkyc
conda install -c conda-forge dlib -y
cd backend
pip install -r requirements.txt
```

Create backend/.env:

```
DATABASE_URL=postgresql+psycopg2://postgres:<password>@localhost:5432/vkycdb
ADMIN_SECRET_KEY=<any-string-for-admin-registration>
FRONTEND_URL=http://localhost:5173
BACKEND_PUBLIC_URL=http://localhost:8000
AGORA_APP_ID=<your-agora-app-id>
AGORA_APP_CERTIFICATE=<your-agora-app-certificate>
SECRET_KEY=<jwt-signing-secret>
```

Start the server:

```
python main.py
```

The backend runs on http://localhost:8000 (Swagger UI at /docs).

4. Frontend

```
cd frontend
npm install
npm run dev
```

The frontend runs on http://localhost:5173.

5. Create an Admin Account

Register a user from the Admin Agent tab and enter the ADMIN_SECRET_KEY value from your .env.


## Known Limitations and Honest Notes

- Aadhaar Secure QR (new format) is not fully decoded. Modern Aadhaar QRs are digitally signed and encoded in a UIDAI-specific binary format that requires the official decoder. The QR pipeline successfully decodes plain-XML Aadhaar QRs (older format) and gracefully falls back to OCR-vs-DB name matching otherwise.
- CPU-only inference. All ML models run on CPU (developed on an AMD Ryzen 5 with integrated graphics). Deepfake / face-match latency is therefore ~2-4 seconds per chunk. With CUDA this drops to sub-second.
- JWT tokens expire after 30 minutes by default. Increase ACCESS_TOKEN_EXPIRE_MINUTES in app/auth/auth.py for longer demos.
- Liveness uses a simple blink/EAR challenge. Production systems would add randomized challenges (head turns, smile, etc.).


## Team

This project was developed as a final-year engineering project by a team of four:

- Gagan A J - backend, ML integration, document and face-match pipeline, video call wiring
- Shashank Patil R
- Krishna Koushik
- Sharath S

This repository is my (Gagan's) personal rebuild and reorganization of the project, including the MySQL to PostgreSQL migration, replacement of the broken pyzbar QR pipeline with an OpenCV + zxing-cpp multi-method decoder, OCR-based name matching, Tesseract path resolution, and a refreshed frontend result UI.


## License

This project is released for educational and portfolio purposes. It is not affiliated with UIDAI or Aadhaar.
