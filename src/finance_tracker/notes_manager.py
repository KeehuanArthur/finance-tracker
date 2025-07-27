import json
import hashlib
import os
from typing import Dict, Optional, Any
from datetime import datetime
import pandas as pd
import fcntl
import tempfile
import shutil

class NotesManager:
    """Manages transaction notes with persistent storage."""
    
    def __init__(self, notes_file: str = "./data/notes_database.json"):
        self.notes_file = notes_file
        self.notes_data = {
            "transaction_notes": {},
            "metadata": {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        }
        self._ensure_notes_file_exists()
        self.load_notes()
    
    def _ensure_notes_file_exists(self):
        """Ensure the notes file and its directory exist."""
        os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)
        if not os.path.exists(self.notes_file):
            self._save_notes_to_file()
    
    def generate_transaction_id(self, row: pd.Series) -> str:
        """Generate a unique transaction ID from transaction data."""
        # Use key fields to create a unique identifier
        key_fields = [
            str(row.get('date', '')),
            str(row.get('amount', '')),
            str(row.get('description', '')),
            str(row.get('bank', '')),
            str(row.get('source_file', ''))
        ]
        
        # Create hash from concatenated fields
        combined_string = '|'.join(key_fields)
        transaction_id = hashlib.sha256(combined_string.encode()).hexdigest()[:16]
        
        return transaction_id
    
    def add_transaction_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add transaction IDs to a DataFrame."""
        if df.empty:
            return df
            
        df_with_ids = df.copy()
        df_with_ids['transaction_id'] = df_with_ids.apply(self.generate_transaction_id, axis=1)
        return df_with_ids
    
    def load_notes(self) -> Dict[str, Any]:
        """Load notes from the JSON file with file locking."""
        try:
            with open(self.notes_file, 'r') as f:
                # Use file locking to prevent concurrent access issues
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                self.notes_data = json.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading notes file: {e}. Using default structure.")
            self._save_notes_to_file()
        except Exception as e:
            print(f"Unexpected error loading notes: {e}")
            
        return self.notes_data
    
    def _save_notes_to_file(self):
        """Save notes to file with atomic write and file locking."""
        try:
            # Update metadata
            self.notes_data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Use atomic write to prevent corruption
            temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                dir=os.path.dirname(self.notes_file),
                delete=False
            )
            
            try:
                # Write to temporary file with locking
                fcntl.flock(temp_file.fileno(), fcntl.LOCK_EX)
                json.dump(self.notes_data, temp_file, indent=2, ensure_ascii=False)
                fcntl.flock(temp_file.fileno(), fcntl.LOCK_UN)
                temp_file.flush()
                os.fsync(temp_file.fileno())
                temp_file.close()
                
                # Atomic move to final location
                shutil.move(temp_file.name, self.notes_file)
                
            except Exception as e:
                # Clean up temp file on error
                temp_file.close()
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                raise e
                
        except Exception as e:
            print(f"Error saving notes file: {e}")
    
    def get_note(self, transaction_id: str) -> str:
        """Get note for a specific transaction ID."""
        return self.notes_data.get("transaction_notes", {}).get(transaction_id, "")
    
    def set_note(self, transaction_id: str, note: str) -> bool:
        """Set note for a specific transaction ID."""
        try:
            if "transaction_notes" not in self.notes_data:
                self.notes_data["transaction_notes"] = {}
            
            # Store the note (empty string removes the note)
            if note.strip():
                self.notes_data["transaction_notes"][transaction_id] = note.strip()
            else:
                # Remove empty notes to keep database clean
                self.notes_data["transaction_notes"].pop(transaction_id, None)
            
            self._save_notes_to_file()
            return True
            
        except Exception as e:
            print(f"Error setting note for transaction {transaction_id}: {e}")
            return False
    
    def get_all_notes(self) -> Dict[str, str]:
        """Get all notes as a dictionary."""
        return self.notes_data.get("transaction_notes", {})
    
    def add_notes_to_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add notes column to DataFrame based on transaction IDs."""
        if df.empty:
            return df
            
        df_with_notes = df.copy()
        
        # Add transaction IDs if not present
        if 'transaction_id' not in df_with_notes.columns:
            df_with_notes = self.add_transaction_ids(df_with_notes)
        
        # Add notes column
        df_with_notes['notes'] = df_with_notes['transaction_id'].apply(self.get_note)
        
        return df_with_notes
    
    def update_notes_from_dataframe(self, df: pd.DataFrame) -> Dict[str, bool]:
        """Update notes from a DataFrame with transaction_id and notes columns."""
        results = {}
        
        if df.empty or 'transaction_id' not in df.columns or 'notes' not in df.columns:
            return results
        
        for _, row in df.iterrows():
            transaction_id = row['transaction_id']
            note = str(row.get('notes', ''))
            results[transaction_id] = self.set_note(transaction_id, note)
        
        return results
    
    def search_notes(self, search_term: str) -> Dict[str, str]:
        """Search for notes containing the search term."""
        if not search_term.strip():
            return {}
            
        search_term_lower = search_term.lower()
        matching_notes = {}
        
        for transaction_id, note in self.notes_data.get("transaction_notes", {}).items():
            if search_term_lower in note.lower():
                matching_notes[transaction_id] = note
                
        return matching_notes
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the notes database."""
        notes = self.notes_data.get("transaction_notes", {})
        
        return {
            "total_notes": len(notes),
            "total_characters": sum(len(note) for note in notes.values()),
            "average_note_length": sum(len(note) for note in notes.values()) / len(notes) if notes else 0,
            "last_updated": self.notes_data.get("metadata", {}).get("last_updated"),
            "database_version": self.notes_data.get("metadata", {}).get("version")
        }
    
    def backup_notes(self, backup_path: str) -> bool:
        """Create a backup of the notes database."""
        try:
            backup_data = self.notes_data.copy()
            backup_data["metadata"]["backup_created"] = datetime.now().isoformat()
            
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def clear_all_notes(self) -> bool:
        """Clear all notes (use with caution)."""
        try:
            self.notes_data["transaction_notes"] = {}
            self._save_notes_to_file()
            return True
            
        except Exception as e:
            print(f"Error clearing notes: {e}")
            return False