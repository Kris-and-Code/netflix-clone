# Netflix Clone Backend

A robust backend API service that replicates core Netflix functionalities, built with Python, FastAPI, and Firebase Realtime Database.

## Features

- 🔐 User Authentication
  - Registration and Login
  - JWT-based authorization
  - Firebase Authentication integration

- 📺 Content Management
  - Movies and TV Series
  - Genre-based filtering
  - Content details (cast, director, ratings, etc.)
  - CRUD operations for content

- 👤 User Profiles
  - Personal watchlist ("My List")
  - Profile management
  - Watch history tracking

## Tech Stack

- **Backend**: Python 3.8+
- **Framework**: FastAPI
- **Database**: Firebase Realtime Database
- **Authentication**: Firebase Auth + JWT
- **Password Hashing**: bcrypt
- **Data Validation**: Pydantic
- **API Documentation**: Auto-generated with FastAPI

## Prerequisites

- Python 3.8 or higher
- Firebase project with Realtime Database enabled
- Firebase service account credentials

## Firebase Setup

### Quick Setup

Run the setup helper script to get started quickly:

```bash
python setup_firebase.py
```

### Manual Setup

#### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing one
3. **Important**: Enable Realtime Database (NOT Firestore)
4. Set database rules (see Security Rules section below)

#### 2. Get Service Account Credentials

1. Go to Project Settings > Service Accounts
2. Click "Generate new private key"
3. Download the JSON file
4. Extract the required values for your `.env` file

#### 3. Enable Authentication

1. Go to Authentication > Sign-in method
2. Enable Email/Password authentication
3. Optionally enable other providers

### Testing & Initialization

After setup, test your connection and initialize the database:

```bash
# Test Firebase connection
python test_firebase_connection.py

# Initialize database with sample data
python init_database.py
```

## Project Structure

```
netflix-clone/
├── app/                    # FastAPI application
│   ├── config/            # Configuration settings
│   ├── models/            # Data models
│   ├── routes/            # API endpoints
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── tests/                  # Test files
├── docker/                 # Docker configuration
├── setup_firebase.py      # Firebase setup helper
├── test_firebase_connection.py  # Connection test script
├── init_database.py       # Database initialization
├── FIREBASE_REALTIME_DB_SETUP.md  # Detailed setup guide
└── firebase-config.json.example  # Firebase config template
```

## Installation
```bash
git clone https://github.com/Kris-and-Code/netflix-clone.git
cd netflix-clone
```

2. Create and activate virtual environment
```bash
python -m venv netflix-env
# On Windows:
netflix-env\Scripts\activate
# On macOS/Linux:
source netflix-env/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your Firebase credentials:

```env
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----"
FIREBASE_CLIENT_EMAIL=your-service-account-email
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account-email
FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.firebaseio.com/

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379

# Optional: AWS S3 for video storage
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_BUCKET_NAME=your-bucket-name
```

## Running the Application

1. Make sure your virtual environment is activated
2. Run the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. The API will be available at:
   - Main API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Firebase Security Rules

### Realtime Database Rules

```json
{
  "rules": {
    "users": {
      "$uid": {
        ".read": "$uid === auth.uid",
        ".write": "$uid === auth.uid"
      }
    },
    "user_emails": {
      ".read": "auth != null",
      ".write": "auth != null"
    },
    "content": {
      ".read": "auth != null",
      ".write": "auth != null"
    },
    "content_by_type": {
      ".read": "auth != null"
    },
    "content_by_genre": {
      ".read": "auth != null"
    }
  }
}
```

### Authentication Rules

- Email/Password authentication enabled
- Users can only access their own data
- Content is readable by authenticated users
- Content creation/updates require authentication

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout

### Content
- `GET /api/v1/content/` - List content with filters
- `GET /api/v1/content/{content_id}` - Get content by ID
- `POST /api/v1/content/` - Create new content
- `PUT /api/v1/content/{content_id}` - Update content
- `DELETE /api/v1/content/{content_id}` - Delete content

### User Profile
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `GET /api/v1/users/my-list` - Get user's watchlist
- `POST /api/v1/users/my-list/{content_id}` - Add to watchlist
- `DELETE /api/v1/users/my-list/{content_id}` - Remove from watchlist

## Database Structure

The Firebase Realtime Database uses the following structure:

```
/
├── users/
│   ├── {user_id}/
│   │   ├── email
│   │   ├── profile_name
│   │   ├── preferences
│   │   ├── my_list/
│   │   │   └── {content_id}: true
│   │   ├── created_at
│   │   └── updated_at
├── user_emails/
│   └── {email}: {user_id}
├── content/
│   ├── {content_id}/
│   │   ├── title
│   │   ├── description
│   │   ├── type
│   │   ├── genre
│   │   ├── release_year
│   │   ├── duration
│   │   ├── thumbnail_url
│   │   ├── video_url
│   │   ├── rating
│   │   ├── content_rating
│   │   ├── created_at
│   │   └── updated_at
├── content_by_type/
│   └── {type}/
│       └── {content_id}: true
└── content_by_genre/
    └── {genre}/
        └── {content_id}: true
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
# Install black if not already installed
pip install black

# Format code
black app/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
