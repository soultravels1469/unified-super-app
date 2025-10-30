from datetime import datetime
from typing import Optional

class ActivityLogger:
    def __init__(self, db):
        self.db = db
    
    async def log_activity(
        self,
        module: str,
        action: str,
        user: str,
        details: Optional[dict] = None
    ):
        """Log user activity"""
        try:
            log_entry = {
                "module": module,
                "action": action,
                "user": user,
                "details": details or {},
                "timestamp": datetime.utcnow()
            }
            await self.db.activity_logs.insert_one(log_entry)
        except Exception as e:
            print(f"Failed to log activity: {e}")
    
    async def get_logs(self, limit: int = 100, module: Optional[str] = None):
        """Get activity logs"""
        query = {}
        if module:
            query["module"] = module
        
        logs = await self.db.activity_logs.find(query).sort("timestamp", -1).limit(limit).to_list(None)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs
