import firebase_admin
from firebase_admin import credentials, db, auth
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK only if configuration is available
db_ref = None
firebase_initialized = False

def initialize_firebase():
    """Initialize Firebase Admin SDK if configuration is available"""
    global db_ref, firebase_initialized
    
    if firebase_initialized:
        return db_ref
    
    # Check if all required Firebase configuration is available
    required_config = [
        os.getenv('FIREBASE_PROJECT_ID'),
        os.getenv('FIREBASE_PRIVATE_KEY_ID'),
        os.getenv('FIREBASE_PRIVATE_KEY'),
        os.getenv('FIREBASE_CLIENT_EMAIL'),
        os.getenv('FIREBASE_CLIENT_ID'),
        os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
    ]
    
    if not all(required_config):
        logger.warning("Firebase configuration incomplete. Firebase features will be disabled.")
        return None
    
    try:
        # Create credentials dictionary
        cred_dict = {
            "type": "service_account",
            "project_id": os.getenv('FIREBASE_PROJECT_ID'),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.getenv('FIREBASE_CLIENT_ID'),
            "auth_uri": os.getenv('FIREBASE_AUTH_URI', "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv('FIREBASE_TOKEN_URI', "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
        }
        
        cred = credentials.Certificate(cred_dict)
        
        # Use provided database URL or generate default one
        database_url = os.getenv('FIREBASE_DATABASE_URL') or f'https://{os.getenv("FIREBASE_PROJECT_ID")}-default-rtdb.firebaseio.com/'
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
        
        # Get Realtime Database reference
        db_ref = db.reference()
        firebase_initialized = True
        logger.info("Firebase Realtime Database initialized successfully")
        return db_ref
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        db_ref = None
        return None

# Try to initialize Firebase on module import
initialize_firebase()

class FirebaseDB:
    """Firebase Realtime Database operations"""
    
    @staticmethod
    def _check_initialization():
        """Check if Firebase is initialized"""
        if not firebase_initialized or not db_ref:
            raise RuntimeError("Firebase is not initialized. Please check your configuration.")
    
    @staticmethod
    async def create_user(user_data: Dict[str, Any]) -> str:
        """Create a new user in the database"""
        FirebaseDB._check_initialization()
        
        try:
            # Generate a unique ID for the user
            import uuid
            user_id = str(uuid.uuid4())
            
            # Add metadata
            user_data['id'] = user_id
            user_data['created_at'] = datetime.utcnow().isoformat()
            user_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Store user data
            db_ref.child('users').child(user_id).set(user_data)
            
            # Create email index for quick lookups
            db_ref.child('user_emails').child(user_data['email'].lower()).set(user_id)
            
            return user_id
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email using email index"""
        FirebaseDB._check_initialization()
        
        try:
            # Get user ID from email index
            user_id = db_ref.child('user_emails').child(email.lower()).get()
            if not user_id:
                return None
            
            # Get user data
            user_data = db_ref.child('users').child(user_id).get()
            if user_data:
                return user_data
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        FirebaseDB._check_initialization()
        
        try:
            user_data = db_ref.child('users').child(user_id).get()
            if user_data:
                return user_data
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            raise
    
    @staticmethod
    async def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        FirebaseDB._check_initialization()
        
        try:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            db_ref.child('users').child(user_id).update(update_data)
            return True
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise
    
    @staticmethod
    async def create_content(content_data: Dict[str, Any]) -> str:
        """Create a new content item in the database"""
        FirebaseDB._check_initialization()
        
        try:
            # Generate a unique ID for the content
            import uuid
            content_id = str(uuid.uuid4())
            
            # Add metadata
            content_data['id'] = content_id
            content_data['created_at'] = datetime.utcnow().isoformat()
            content_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Store content data
            db_ref.child('content').child(content_id).set(content_data)
            
            # Create indexes for quick filtering
            if 'type' in content_data:
                db_ref.child('content_by_type').child(content_data['type']).child(content_id).set(True)
            
            if 'genre' in content_data and isinstance(content_data['genre'], list):
                for genre in content_data['genre']:
                    db_ref.child('content_by_genre').child(genre).child(content_id).set(True)
            
            return content_id
        except Exception as e:
            logger.error(f"Error creating content: {str(e)}")
            raise
    
    @staticmethod
    async def get_content_by_id(content_id: str) -> Optional[Dict[str, Any]]:
        """Get content by ID"""
        FirebaseDB._check_initialization()
        
        try:
            content_data = db_ref.child('content').child(content_id).get()
            if content_data:
                return content_data
            return None
        except Exception as e:
            logger.error(f"Error getting content by ID: {str(e)}")
            raise
    
    @staticmethod
    async def get_content_list(
        content_type: Optional[str] = None,
        genre: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get paginated content list with optional filters"""
        FirebaseDB._check_initialization()
        
        try:
            content_list = []
            
            if content_type:
                # Get content IDs by type
                type_index = db_ref.child('content_by_type').child(content_type).get()
                if type_index:
                    content_ids = list(type_index.keys())
                else:
                    return [], 0
            elif genre:
                # Get content IDs by genre
                genre_index = db_ref.child('content_by_genre').child(genre).get()
                if genre_index:
                    content_ids = list(genre_index.keys())
                else:
                    return [], 0
            else:
                # Get all content IDs
                content_index = db_ref.child('content').get()
                if content_index:
                    content_ids = list(content_index.keys())
                else:
                    return [], 0
            
            # Get total count
            total = len(content_ids)
            
            # Apply pagination
            paginated_ids = content_ids[offset:offset + limit]
            
            # Get content data for paginated IDs
            for content_id in paginated_ids:
                content_data = db_ref.child('content').child(content_id).get()
                if content_data:
                    content_list.append(content_data)
            
            return content_list, total
        except Exception as e:
            logger.error(f"Error getting content list: {str(e)}")
            raise
    
    @staticmethod
    async def update_content(content_id: str, update_data: Dict[str, Any]) -> bool:
        """Update content data"""
        FirebaseDB._check_initialization()
        
        try:
            update_data['updated_at'] = datetime.utcnow().isoformat()
            db_ref.child('content').child(content_id).update(update_data)
            
            # Update indexes if type or genre changed
            if 'type' in update_data:
                # Remove from old type index
                old_content = db_ref.child('content').child(content_id).get()
                if old_content and 'type' in old_content:
                    db_ref.child('content_by_type').child(old_content['type']).child(content_id).delete()
                
                # Add to new type index
                db_ref.child('content_by_type').child(update_data['type']).child(content_id).set(True)
            
            if 'genre' in update_data:
                # Remove from old genre indexes
                old_content = db_ref.child('content').child(content_id).get()
                if old_content and 'genre' in old_content and isinstance(old_content['genre'], list):
                    for genre in old_content['genre']:
                        db_ref.child('content_by_genre').child(genre).child(content_id).delete()
                
                # Add to new genre indexes
                if isinstance(update_data['genre'], list):
                    for genre in update_data['genre']:
                        db_ref.child('content_by_genre').child(genre).child(content_id).set(True)
            
            return True
        except Exception as e:
            logger.error(f"Error updating content: {str(e)}")
            raise
    
    @staticmethod
    async def delete_content(content_id: str) -> bool:
        """Delete content and remove from indexes"""
        FirebaseDB._check_initialization()
        
        try:
            # Get content data before deletion for index cleanup
            content_data = db_ref.child('content').child(content_id).get()
            
            # Delete from main content node
            db_ref.child('content').child(content_id).delete()
            
            # Remove from type index
            if content_data and 'type' in content_data:
                db_ref.child('content_by_type').child(content_data['type']).child(content_id).delete()
            
            # Remove from genre indexes
            if content_data and 'genre' in content_data and isinstance(content_data['genre'], list):
                for genre in content_data['genre']:
                    db_ref.child('content_by_genre').child(genre).child(content_id).delete()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting content: {str(e)}")
            raise
    
    @staticmethod
    async def add_to_user_list(user_id: str, content_id: str) -> bool:
        """Add content to user's my_list"""
        FirebaseDB._check_initialization()
        
        try:
            db_ref.child('users').child(user_id).child('my_list').child(content_id).set(True)
            return True
        except Exception as e:
            logger.error(f"Error adding to user list: {str(e)}")
            raise
    
    @staticmethod
    async def remove_from_user_list(user_id: str, content_id: str) -> bool:
        """Remove content from user's my_list"""
        FirebaseDB._check_initialization()
        
        try:
            db_ref.child('users').child(user_id).child('my_list').child(content_id).delete()
            return True
        except Exception as e:
            logger.error(f"Error removing from user list: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_list(user_id: str) -> List[Dict[str, Any]]:
        """Get user's my_list content"""
        FirebaseDB._check_initialization()
        
        try:
            my_list_ref = db_ref.child('users').child(user_id).child('my_list').get()
            if not my_list_ref:
                return []
            
            content_ids = list(my_list_ref.keys())
            content_list = []
            
            for content_id in content_ids:
                content_data = db_ref.child('content').child(content_id).get()
                if content_data:
                    content_list.append(content_data)
            
            return content_list
        except Exception as e:
            logger.error(f"Error getting user list: {str(e)}")
            raise

# Firebase Authentication utilities
class FirebaseAuth:
    """Firebase Authentication operations"""
    
    @staticmethod
    def _check_initialization():
        """Check if Firebase is initialized"""
        if not firebase_initialized:
            raise RuntimeError("Firebase is not initialized. Please check your configuration.")
    
    @staticmethod
    async def verify_id_token(id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token"""
        FirebaseAuth._check_initialization()
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Error verifying ID token: {str(e)}")
            raise
    
    @staticmethod
    async def create_custom_token(uid: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """Create custom token for user"""
        FirebaseAuth._check_initialization()
        
        try:
            token = auth.create_custom_token(uid, additional_claims or {})
            return token.decode() if isinstance(token, bytes) else token
        except Exception as e:
            logger.error(f"Error creating custom token: {str(e)}")
            raise
