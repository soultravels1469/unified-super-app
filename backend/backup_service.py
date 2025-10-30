import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import shutil

class BackupService:
    def __init__(self, db, activity_logger):
        self.db = db
        self.activity_logger = activity_logger
        self.backup_dir = Path(__file__).resolve().parent / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = 7
        
    async def create_backup(self, user: str = "system", backup_type: str = "automatic") -> Dict:
        """Create a full database backup"""
        try:
            timestamp = datetime.utcnow()
            backup_filename = f"backup_{timestamp.strftime('%Y_%m_%d_%H_%M_%S')}.json"
            backup_path = self.backup_dir / backup_filename
            
            # Collections to backup
            collections = [
                "revenues", "expenses", "users", "leads", "reminders",
                "vendors", "bank_accounts", "settings", "activity_logs",
                "accounts", "ledgers", "gst_records"
            ]
            
            backup_data = {
                "timestamp": timestamp.isoformat(),
                "version": "1.0",
                "collections": {}
            }
            
            # Export each collection
            for collection_name in collections:
                try:
                    docs = await self.db[collection_name].find({}).to_list(None)
                    # Convert ObjectId to string for JSON serialization
                    for doc in docs:
                        if '_id' in doc:
                            doc['_id'] = str(doc['_id'])
                    backup_data["collections"][collection_name] = docs
                except Exception as e:
                    print(f"Warning: Failed to backup {collection_name}: {e}")
                    backup_data["collections"][collection_name] = []
            
            # Write to file
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, default=str, indent=2)
            
            # Log activity
            await self.activity_logger.log_activity(
                module="Backup",
                action=f"backup_{backup_type}",
                user=user,
                details={
                    "filename": backup_filename,
                    "collections_count": len(collections),
                    "file_size_mb": round(backup_path.stat().st_size / (1024 * 1024), 2)
                }
            )
            
            # Cleanup old backups
            await self.cleanup_old_backups()
            
            return {
                "success": True,
                "filename": backup_filename,
                "timestamp": timestamp.isoformat(),
                "collections": len(collections),
                "size_mb": round(backup_path.stat().st_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            await self.activity_logger.log_activity(
                module="Backup",
                action="backup_failed",
                user=user,
                details={"error": str(e)}
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    async def restore_backup(self, filename: str, user: str = "admin") -> Dict:
        """Restore database from backup file"""
        try:
            backup_path = self.backup_dir / filename
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {filename}")
            
            # Read backup file
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            collections_restored = 0
            
            # Restore each collection
            for collection_name, docs in backup_data["collections"].items():
                if docs:  # Only restore if collection has data
                    try:
                        # Clear existing collection
                        await self.db[collection_name].delete_many({})
                        
                        # Insert backup data
                        if docs:
                            await self.db[collection_name].insert_many(docs)
                        
                        collections_restored += 1
                    except Exception as e:
                        print(f"Warning: Failed to restore {collection_name}: {e}")
            
            # Log activity
            await self.activity_logger.log_activity(
                module="Backup",
                action="restore",
                user=user,
                details={
                    "filename": filename,
                    "collections_restored": collections_restored,
                    "backup_timestamp": backup_data.get("timestamp")
                }
            )
            
            return {
                "success": True,
                "filename": filename,
                "collections_restored": collections_restored,
                "backup_timestamp": backup_data.get("timestamp")
            }
            
        except Exception as e:
            await self.activity_logger.log_activity(
                module="Backup",
                action="restore_failed",
                user=user,
                details={"error": str(e), "filename": filename}
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("backup_*.json"), reverse=True):
            try:
                stat = backup_file.stat()
                backups.append({
                    "filename": backup_file.name,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "age_days": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                })
            except Exception as e:
                print(f"Error reading backup {backup_file.name}: {e}")
        
        return backups
    
    async def cleanup_old_backups(self):
        """Remove backups older than max_backups count"""
        try:
            backups = sorted(self.backup_dir.glob("backup_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the last N backups
            for old_backup in backups[self.max_backups:]:
                old_backup.unlink()
                print(f"Deleted old backup: {old_backup.name}")
        
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    async def schedule_daily_backup(self):
        """Background task for daily backups at midnight"""
        while True:
            try:
                now = datetime.now()
                # Calculate time until next midnight
                tomorrow = now + timedelta(days=1)
                midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
                seconds_until_midnight = (midnight - now).total_seconds()
                
                # Wait until midnight
                await asyncio.sleep(seconds_until_midnight)
                
                # Create backup
                await self.create_backup(user="system", backup_type="automatic")
                
            except Exception as e:
                print(f"Scheduled backup error: {e}")
                await asyncio.sleep(3600)  # Retry after 1 hour on error
