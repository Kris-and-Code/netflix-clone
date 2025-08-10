# Firebase Realtime Database Setup Guide

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

### 2. Enable Realtime Database (NOT Firestore)
1. In Firebase Console, go to "Realtime Database" (not Firestore)
2. Click "Create database"
3. Choose "Start in test mode" for development
4. Select a location close to your users
5. **Important**: Make sure you're creating a Realtime Database, not Firestore

### 3. Enable Authentication
1. In Firebase Console, go to "Authentication"
2. Click "Get started"
3. Enable "Email/Password" sign-in method

### 4. Create Service Account
1. In Firebase Console, go to Project Settings (gear icon)
2. Go to "Service accounts" tab
3. Click "Generate new private key"
4. Download the JSON file
5. Copy the contents to your `.env` file or use the JSON file directly

### 5. Environment Variables
Create a `.env` file in your project root with:

```env
# API Settings
SECRET_KEY=your-secret-key-here-make-it-long-and-random
DEBUG=True

# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account-email@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account-email%40your-project.iam.gserviceaccount.com
FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.firebaseio.com
```

### 6. Install Dependencies
```bash
pip install -r requirements.txt
```

### 7. Run the Application
```bash
python -m uvicorn app.main:app --reload
```

## Firebase Realtime Database Security Rules

### Database Rules
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
      ".write": "auth != null && root.child('users').child(auth.uid).child('role').val() === 'admin'"
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
- Password requirements: min 8 chars, uppercase, lowercase, number, special char
- Rate limiting: 5 registrations per hour, 10 logins per 5 minutes

## Database Structure

The Realtime Database will have the following structure:

```
netflix-clone/
├── users/
│   ├── {user_id}/
│   │   ├── id
│   │   ├── email
│   │   ├── username
│   │   ├── created_at
│   │   ├── updated_at
│   │   ├── my_list/
│   │   │   ├── {content_id}: true
│   │   │   └── ...
│   │   └── preferences/
├── user_emails/
│   ├── {email}: {user_id}
├── content/
│   ├── {content_id}/
│   │   ├── id
│   │   ├── title
│   │   ├── description
│   │   ├── type (movie/series)
│   │   ├── genre
│   │   ├── release_year
│   │   ├── rating
│   │   ├── created_by
│   │   ├── created_at
│   │   └── updated_at
├── content_by_type/
│   ├── movie/
│   │   ├── {content_id}: true
│   └── series/
│       ├── {content_id}: true
└── content_by_genre/
    ├── action/
    │   ├── {content_id}: true
    ├── comedy/
    │   ├── {content_id}: true
    └── drama/
        ├── {content_id}: true
```

## Features
- ✅ User registration and authentication
- ✅ JWT token management
- ✅ Content CRUD operations
- ✅ User profiles and preferences
- ✅ My List functionality
- ✅ Rate limiting
- ✅ Firebase Realtime Database integration
- ✅ Firebase Authentication support
- ✅ Real-time data synchronization
- ✅ Offline support

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

## Testing Firebase Connection

Run the test file to verify your Firebase connection:

```bash
python test_firebase.py
```

## Troubleshooting

### Common Issues:
1. **Database URL**: Make sure you're using Realtime Database URL, not Firestore
2. **Service Account**: Ensure the service account has proper permissions
3. **Rules**: Check that your database rules allow read/write operations
4. **Environment Variables**: Verify all Firebase variables are set correctly

### Database URL Format:
- Realtime Database: `https://{project-id}-default-rtdb.firebaseio.com`
- Firestore: `https://firestore.googleapis.com/v1/projects/{project-id}/databases/(default)`

## Next Steps
1. Set up your Firebase project
2. Configure environment variables
3. Test the connection
4. Start building your Netflix clone features
