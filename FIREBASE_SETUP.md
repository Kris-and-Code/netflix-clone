# Firebase Setup Guide

## Prerequisites
1. Google Cloud Project
2. Firebase project enabled
3. Service account key

## Setup Steps

### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Enter project name (e.g., "netflix-clone")
4. Follow the setup wizard

### 2. Enable Firestore Database
1. In Firebase Console, go to "Firestore Database"
2. Click "Create database"
3. Choose "Start in test mode" for development
4. Select a location close to your users

### 3. Enable Authentication
1. In Firebase Console, go to "Authentication"
2. Click "Get started"
3. Enable "Email/Password" sign-in method

### 4. Create Service Account
1. In Firebase Console, go to Project Settings (gear icon)
2. Go to "Service accounts" tab
3. Click "Generate new private key"
4. Download the JSON file

### 5. Environment Variables
Create a `.env` file in your project root with:

```env
# API Settings
SECRET_KEY=your-secret-key-here
DEBUG=True




# Redis Configuration (optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# AWS S3 Configuration (optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_BUCKET_NAME=your-s3-bucket-name
```

### 6. Install Dependencies
```bash
pip install -r requirements.txt
```

### 7. Run the Application
```bash
python -m uvicorn app.main:app --reload
```

## Firebase Security Rules

### Firestore Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Content is readable by all authenticated users
    // Only creators can modify their content
    match /content/{contentId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && 
        request.auth.uid == resource.data.created_by;
    }
  }
}
```

### Authentication Rules
- Email/Password authentication enabled
- Password requirements: min 8 chars, uppercase, lowercase, number, special char
- Rate limiting: 5 registrations per hour, 10 logins per 5 minutes

## Features
- ✅ User registration and authentication
- ✅ JWT token management
- ✅ Content CRUD operations
- ✅ User profiles and preferences
- ✅ My List functionality
- ✅ Rate limiting
- ✅ Firebase Firestore integration
- ✅ Firebase Authentication support

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh-token` - Refresh access token
- `POST /api/auth/logout` - User logout

### Content
- `GET /api/content/` - List content with pagination
- `GET /api/content/{id}` - Get content by ID
- `POST /api/content/` - Create new content
- `PUT /api/content/{id}` - Update content
- `DELETE /api/content/{id}` - Delete content

### User
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile
- `GET /api/user/my-list` - Get user's my list
- `POST /api/user/my-list/{id}` - Add content to my list
- `DELETE /api/user/my-list/{id}` - Remove content from my list
