"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (within date range)"""
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Find announcements that are currently active
        announcements = list(announcements_collection.find({
            "$or": [
                {"start_date": {"$exists": False}},
                {"start_date": {"$lte": current_date}}
            ],
            "end_date": {"$gte": current_date}
        }))
        
        # Convert ObjectId to string for JSON serialization
        for announcement in announcements:
            announcement["_id"] = str(announcement["_id"])
        
        return announcements
    except Exception as e:
        print(f"Error fetching announcements: {e}")
        return []


@router.get("/all")
def get_all_announcements(username: str) -> List[Dict[str, Any]]:
    """Get all announcements (for management). Requires authentication."""
    try:
        # Verify user is authenticated
        teacher = teachers_collection.find_one({"_id": username})
        if not teacher:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Get all announcements
        announcements = list(announcements_collection.find({}))
        
        # Convert ObjectId to string for JSON serialization
        for announcement in announcements:
            announcement["_id"] = str(announcement["_id"])
        
        return announcements
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching all announcements: {e}")
        return []


@router.post("")
def create_announcement(
    message: str,
    end_date: str,
    username: str,
    start_date: str = None
) -> Dict[str, Any]:
    """Create a new announcement. Requires authentication."""
    try:
        # Verify user is authenticated
        teacher = teachers_collection.find_one({"_id": username})
        if not teacher:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Validate end_date is in the future
        if end_date < datetime.now().strftime("%Y-%m-%d"):
            raise HTTPException(status_code=400, detail="End date must be in the future")
        
        # Create announcement
        announcement = {
            "message": message,
            "start_date": start_date or datetime.now().strftime("%Y-%m-%d"),
            "end_date": end_date,
            "created_by": username,
            "created_at": datetime.now().isoformat() + "Z"
        }
        
        result = announcements_collection.insert_one(announcement)
        announcement["_id"] = str(result.inserted_id)
        
        return announcement
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating announcement: {e}")
        raise HTTPException(status_code=500, detail="Failed to create announcement")


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    message: str,
    end_date: str,
    username: str,
    start_date: str = None
) -> Dict[str, str]:
    """Update an existing announcement. Requires authentication."""
    try:
        # Verify user is authenticated
        teacher = teachers_collection.find_one({"_id": username})
        if not teacher:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Update announcement
        update_data = {
            "message": message,
            "end_date": end_date
        }
        
        if start_date:
            update_data["start_date"] = start_date
        
        result = announcements_collection.update_one(
            {"_id": ObjectId(announcement_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        return {"message": "Announcement updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating announcement: {e}")
        raise HTTPException(status_code=500, detail="Failed to update announcement")


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, username: str) -> Dict[str, str]:
    """Delete an announcement. Requires authentication."""
    try:
        # Verify user is authenticated
        teacher = teachers_collection.find_one({"_id": username})
        if not teacher:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Delete announcement
        result = announcements_collection.delete_one({"_id": ObjectId(announcement_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        return {"message": "Announcement deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting announcement: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete announcement")
