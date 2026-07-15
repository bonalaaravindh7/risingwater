# 🌊 Rising Waters — Machine Learning-Based Flood Prediction System

Rising Waters is a Flask web application that predicts flood occurrence from
historical weather and rainfall data. It covers the full ML lifecycle — data
preprocessing, model training, evaluation, and serialization — combined with
user accounts, a persistent prediction history, and server-side validation.

## Features
- 🔐 User authentication (email/password + "Continue with Google")
- 🌧️ Flood prediction from 10 weather & rainfall inputs
- 📊 Animated risk gauge on results (Flood Predicted / No Flood Predicted)
- 🗂️ Prediction history per user, with delete support
- 🌗 Persisted light/dark theme + ambient rain-and-lightning animation
- ✅ CSRF protection and WTForms validation on every form

## Tech Stack
Flask · Flask-SQLAlchemy · Flask-Login · Flask-WTF · scikit-learn ·
Pandas · NumPy · Joblib · Gunicorn · Render (deployment)

## Project Structure
| Folder | Description |
|---|---|
| `1. Brainstorming & Ideation` | Initial concept and problem framing |
| `2. Requirement Analysis` | Functional & non-functional requirements |
| `3. Project Design Phase` | Architecture and design docs |
| `4. Project Planning Phase` | Milestones and planning |
| `5. Project Development Phase` | Source code and implementation |
| `6. Project Testing` | Test cases and validation results |
| `7. Project Documentation` | Full project documentation |
| `8. Project Demonstration` | Demo materials |

## Live Demo
🔗 [risingwaters-1.onrender.com](https://risingwaters-1.onrender.com)

## Demo Video
🎥 [Watch the project walkthrough](https://drive.google.com/file/d/1mrpNulO4c-xLdWXaaDxH9CV9T5jWIXNK/view?usp=sharing)

## Setup
```bash
git clone https://github.com/Laharisrikotipalli/RisingWaters.git
cd RisingWaters
pip install -r requirements.txt
python app.py
```

## Author
**Lahari Sri Kotipalli** — B.Tech, Computer Science and Engineering
