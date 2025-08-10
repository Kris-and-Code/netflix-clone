from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from ..models.content import ContentResponse, ContentCreate, ContentUpdate
from ..models.user import UserResponse
from ..utils.auth import get_current_user
from ..utils.firebase import FirebaseDB
from ..schemas.responses import DataResponse, ErrorResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=DataResponse[List[ContentResponse]])
async def get_content(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    genre: Optional[str] = None,
    content_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get paginated content list with optional filters.
    
    Args:
        page: Page number (1-based)
        limit: Number of items per page
        genre: Filter by genre
        content_type: Filter by content type
        search: Search in title and description
        current_user: Current authenticated user
        
    Returns:
        DataResponse containing paginated content list
    """
    try:
        offset = (page - 1) * limit
        
        # Get content from Firebase
        content_list, total = await FirebaseDB.get_content_list(
            content_type=content_type,
            genre=genre,
            limit=limit,
            offset=offset
        )
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            content_list = [
                content for content in content_list
                if (search_lower in content.get("title", "").lower() or
                    search_lower in content.get("description", "").lower())
            ]
            total = len(content_list)
        
        # Convert to ContentResponse models
        content_responses = []
        for content in content_list:
            content_responses.append(ContentResponse(**content))
        
        return DataResponse(
            success=True,
            message="Content retrieved successfully",
            data=content_responses
        )
    except Exception as e:
        logger.error(f"Error fetching content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch content"
        )

@router.get("/{content_id}", response_model=DataResponse[ContentResponse])
async def get_content_by_id(
    content_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get content by ID.
    
    Args:
        content_id: Content ID
        current_user: Current authenticated user
        
    Returns:
        DataResponse containing content details
    """
    try:
        content = await FirebaseDB.get_content_by_id(content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        content_response = ContentResponse(**content)
        return DataResponse(
            success=True,
            message="Content retrieved successfully",
            data=content_response
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching content by ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch content"
        )

@router.post("/", response_model=DataResponse[ContentResponse])
async def create_content(
    content: ContentCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create new content.
    
    Args:
        content: Content creation data
        current_user: Current authenticated user
        
    Returns:
        DataResponse containing created content
    """
    try:
        content_data = content.model_dump()
        content_data["created_by"] = current_user.id
        
        content_id = await FirebaseDB.create_content(content_data)
        
        # Get the created content
        created_content = await FirebaseDB.get_content_by_id(content_id)
        content_response = ContentResponse(**created_content)
        
        return DataResponse(
            success=True,
            message="Content created successfully",
            data=content_response
        )
    except Exception as e:
        logger.error(f"Error creating content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create content"
        )

@router.put("/{content_id}", response_model=DataResponse[ContentResponse])
async def update_content(
    content_id: str,
    content_update: ContentUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update existing content.
    
    Args:
        content_id: Content ID
        content_update: Content update data
        current_user: Current authenticated user
        
    Returns:
        DataResponse containing updated content
    """
    try:
        # Check if content exists
        existing_content = await FirebaseDB.get_content_by_id(content_id)
        if not existing_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        # Check if user owns the content
        if existing_content.get("created_by") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this content"
            )
        
        # Update content
        update_data = content_update.model_dump(exclude_unset=True)
        await FirebaseDB.update_content(content_id, update_data)
        
        # Get updated content
        updated_content = await FirebaseDB.get_content_by_id(content_id)
        content_response = ContentResponse(**updated_content)
        
        return DataResponse(
            success=True,
            message="Content updated successfully",
            data=content_response
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update content"
        )

@router.delete("/{content_id}", response_model=DataResponse[dict])
async def delete_content(
    content_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete content.
    
    Args:
        content_id: Content ID
        current_user: Current authenticated user
        
    Returns:
        DataResponse confirming deletion
    """
    try:
        # Check if content exists
        existing_content = await FirebaseDB.get_content_by_id(content_id)
        if not existing_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        # Check if user owns the content
        if existing_content.get("created_by") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this content"
            )
        
        # Delete content
        await FirebaseDB.delete_content(content_id)
        
        return DataResponse(
            success=True,
            message="Content deleted successfully",
            data={}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete content"
        ) 