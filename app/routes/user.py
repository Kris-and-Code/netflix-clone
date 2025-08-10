from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from ..models.user import UserResponse, UserUpdate
from ..utils.auth import get_current_user
from ..utils.firebase import FirebaseDB
from ..schemas.responses import DataResponse, ErrorResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/profile", response_model=DataResponse[UserResponse])
async def get_user_profile(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get current user's profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        DataResponse containing user profile
    """
    try:
        user = await FirebaseDB.get_user_by_id(current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_response = UserResponse(**user)
        return DataResponse(
            success=True,
            message="Profile retrieved successfully",
            data=user_response
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch profile"
        )

@router.put("/profile", response_model=DataResponse[UserResponse])
async def update_user_profile(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update current user's profile.
    
    Args:
        user_update: User update data
        current_user: Current authenticated user
        
    Returns:
        DataResponse containing updated user profile
    """
    try:
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Update user in Firebase
        await FirebaseDB.update_user(current_user.id, update_data)
        
        # Get updated user
        updated_user = await FirebaseDB.get_user_by_id(current_user.id)
        user_response = UserResponse(**updated_user)
        
        return DataResponse(
            success=True,
            message="Profile updated successfully",
            data=user_response
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update profile"
        )

@router.post("/my-list/{content_id}", response_model=DataResponse[Dict[str, Any]])
async def add_to_my_list(
    content_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Add content to user's my list.
    
    Args:
        content_id: Content ID to add
        current_user: Current authenticated user
        
    Returns:
        DataResponse confirming addition
    """
    try:
        # Check if content exists
        content = await FirebaseDB.get_content_by_id(content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        # Get current user
        user = await FirebaseDB.get_user_by_id(current_user.id)
        my_list = user.get("my_list", [])
        
        # Check if content is already in list
        if content_id in my_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content already in my list"
            )
        
        # Add to my list
        my_list.append(content_id)
        await FirebaseDB.update_user(current_user.id, {"my_list": my_list})
        
        return DataResponse(
            success=True,
            message="Content added to my list successfully",
            data={"content_id": content_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to my list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not add to my list"
        )

@router.delete("/my-list/{content_id}", response_model=DataResponse[Dict[str, Any]])
async def remove_from_my_list(
    content_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Remove content from user's my list.
    
    Args:
        content_id: Content ID to remove
        current_user: Current authenticated user
        
    Returns:
        DataResponse confirming removal
    """
    try:
        # Get current user
        user = await FirebaseDB.get_user_by_id(current_user.id)
        my_list = user.get("my_list", [])
        
        # Check if content is in list
        if content_id not in my_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content not in my list"
            )
        
        # Remove from my list
        my_list.remove(content_id)
        await FirebaseDB.update_user(current_user.id, {"my_list": my_list})
        
        return DataResponse(
            success=True,
            message="Content removed from my list successfully",
            data={"content_id": content_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from my list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not remove from my list"
        )

@router.get("/my-list", response_model=DataResponse[list])
async def get_my_list(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get user's my list.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        DataResponse containing user's my list
    """
    try:
        user = await FirebaseDB.get_user_by_id(current_user.id)
        my_list = user.get("my_list", [])
        
        return DataResponse(
            success=True,
            message="My list retrieved successfully",
            data=my_list
        )
    except Exception as e:
        logger.error(f"Error fetching my list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch my list"
        )
