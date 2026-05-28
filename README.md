# SecureKYC - AI-Powered vKYC with Deepfake and Liveness Detection

A full-stack video Know-Your-Customer (vKYC) platform that verifies a user's identity in real time during a live video call. Combines document OCR, Aadhaar QR extraction, face matching, liveness detection, and deepfake detection to flag fraudulent verification attempts.

Built as a final-year engineering project. This repository is a personal rebuild and refactor.


## Features

- **Document Verification** - Tesseract OCR extracts the printed name from an Aadhaar / PAN / Voter ID / DL / Passport and cross-checks it against the registered user using fuzzy string matching.
- **Aadhaar QR Extraction** - OpenCV + zxing-cpp with multi-stage preprocessing (grayscale, upscaling, sharpening, Otsu thresholding) decodes the embedded QR; structured fields are parsed via lxml.
- **Live Video Calls** - Agora RTC SDK with camera, mic, screen share, and one-click room creation.
- **Deepfake Detection** - HuggingFace Vision Transformer (prithivMLmods/Deep-Fake-Detector-v2-Model) streams a probability score throughout the call.
- **Liveness Detection** - dlib 68-point landmarks + Eye Aspect Ratio (EAR) detects blinks to reject photos and pre-recorded videos.
- **Face Matching** - DeepFace + FaceNet512 compares the uploaded ID photo against the live feed.
- **Admin Dashboard** - Live AI scoring panel during the call and a persistent audit log of every session.
- **JWT Auth** - Bcrypt password hashing, role-based access (Client / Admin), and a one-time admin secret.


## Tech Stack

**Backend:** Python 3.11, FastAPI, PostgreSQL + SQLAlchemy, PyTorch, TensorFlow + DeepFace, dlib, OpenCV, zxing-cpp, pytesseract, RapidFuzz, WebSockets

**Frontend:** React 19, Vite, Material UI, TailwindCSS, Agora RTC SDK NG, Framer Motion

**Infra:** Git LFS, python-dotenv


## How It Works

1. **Register** - User account stored with bcrypt-hashed password.
2. **Upload ID** - QR-decode pipeline runs, OCR extracts printed text, RapidFuzz checks name against DB.
3. **Video Call** - Agora room opens; browser streams JPEG frames every 500 ms over WebSocket to the backend, which runs deepfake / liveness / face-match models on the fly.
4. **Admin Decision** - Scores stored in verification_results with IP, location, and pass/fail.


## Team

Final-year engineering project by a team of four:

- **Gagan A J** - ML integration and database
- Shashank Patil R
- Krishna Koushik
- Sharath S
