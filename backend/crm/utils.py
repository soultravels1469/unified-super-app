import random
import string
import os
import aiofiles
from datetime import datetime
from typing import Optional


def generate_lead_id() -> str:
    """Generate unique lead ID in format: LD-YYYYMMDD-XXXX"""
    date_part = datetime.utcnow().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"LD-{date_part}-{random_part}"


def generate_referral_code() -> str:
    """Generate short unique referral code (6 characters)"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def validate_file_type(filename: str) -> bool:
    """Validate file type for document upload"""
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.docx'}
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions


def get_upload_path(lead_id: str) -> str:
    """Get upload directory path for a lead"""
    base_path = "/app/backend/uploads/crm"
    lead_path = os.path.join(base_path, lead_id)
    os.makedirs(lead_path, exist_ok=True)
    return lead_path


async def save_upload_file(file, lead_id: str) -> dict:
    """Save uploaded file and return file info"""
    upload_path = get_upload_path(lead_id)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_path, safe_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    return {
        "file_name": file.filename,
        "file_path": f"/uploads/crm/{lead_id}/{safe_filename}",
        "uploaded_at": datetime.utcnow(),
        "size": file_size
    }


def delete_file(file_path: str) -> bool:
    """Delete a file from disk"""
    try:
        full_path = f"/app/backend{file_path}"
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False
