"""
Account & Key Pool Manager for GENAUDIO
Handles multi-account storage, auto-sync, live health verification, smart load balancing and failover.
"""
from __future__ import annotations
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests

SECRETS_POOL_PATH = Path(os.environ.get("ELEVENLABS_KEYS_POOL", str(BASE_DIR / "keys_pool.example.txt")))
BASE_DIR = Path(__file__).resolve().parent.parent
ACCOUNTS_FILE = BASE_DIR / "accounts.json"

class AccountManager:
    def __init__(self, accounts_path: Optional[Path] = None):
        self.accounts_path = accounts_path or ACCOUNTS_FILE
        self.data: Dict[str, Any] = {"accounts": [], "settings": {"strategy": "highest_quota_first", "auto_failover": True}}
        self.load_accounts()
        
        # Auto-import if empty
        if not self.data["accounts"] and SECRETS_POOL_PATH.exists():
            self.auto_import_from_secrets()

    def load_accounts(self) -> None:
        """Load accounts from JSON file."""
        if self.accounts_path.exists():
            try:
                with open(self.accounts_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {"accounts": [], "settings": {"strategy": "highest_quota_first", "auto_failover": True}}
        else:
            self.save_accounts()

    def save_accounts(self) -> None:
        """Persist accounts to JSON file."""
        self.accounts_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.accounts_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def auto_import_from_secrets(self, pool_path: Optional[Path] = None) -> int:
        """Import all sk_ keys from secrets vault into accounts pool."""
        target_path = pool_path or SECRETS_POOL_PATH
        if not target_path.exists():
            return 0
        
        existing_keys = {acc["api_key"] for acc in self.data["accounts"]}
        imported_count = 0
        
        with open(target_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                line = line.strip()
                if "sk_" in line:
                    key = "sk_" + line.split("sk_")[1].strip()
                    if key not in existing_keys:
                        new_acc = {
                            "id": len(self.data["accounts"]) + 1,
                            "name": f"Vault Key #{len(self.data['accounts']) + 1}",
                            "api_key": key,
                            "status": "unverified",
                            "tier": "unknown",
                            "character_limit": 10000,
                            "character_count": 0,
                            "character_remaining": 10000,
                            "last_checked": None
                        }
                        self.data["accounts"].append(new_acc)
                        existing_keys.add(key)
                        imported_count += 1
                        
        if imported_count > 0:
            self.save_accounts()
        return imported_count

    def add_key(self, api_key: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Add a new API key to the pool."""
        api_key = api_key.strip()
        existing = [acc for acc in self.data["accounts"] if acc["api_key"] == api_key]
        if existing:
            return {"success": False, "message": "Key already exists in accounts pool."}
        
        new_id = len(self.data["accounts"]) + 1
        new_name = name or f"Key #{new_id}"
        new_acc = {
            "id": new_id,
            "name": new_name,
            "api_key": api_key,
            "status": "unverified",
            "tier": "unknown",
            "character_limit": 10000,
            "character_count": 0,
            "character_remaining": 10000,
            "last_checked": None
        }
        self.data["accounts"].append(new_acc)
        self.save_accounts()
        
        # Verify immediately
        self.check_single_health(new_id)
        return {"success": True, "account": new_acc}

    def remove_key(self, account_id: int) -> bool:
        """Remove a key by ID."""
        initial_len = len(self.data["accounts"])
        self.data["accounts"] = [acc for acc in self.data["accounts"] if acc["id"] != account_id]
        # Re-index
        for idx, acc in enumerate(self.data["accounts"], 1):
            acc["id"] = idx
        self.save_accounts()
        return len(self.data["accounts"]) < initial_len

    def check_single_health(self, account_id: int) -> Dict[str, Any]:
        """Query ElevenLabs subscription endpoint for a single key."""
        acc = next((a for a in self.data["accounts"] if a["id"] == account_id), None)
        if not acc:
            return {"success": False, "message": "Account not found"}
        
        url = "https://api.elevenlabs.io/v1/user/subscription"
        headers = {"xi-api-key": acc["api_key"]}
        try:
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                sub = res.json()
                limit = sub.get("character_limit", 10000)
                used = sub.get("character_count", 0)
                rem = max(0, limit - used)
                tier = sub.get("tier", "free")
                
                acc["tier"] = tier
                acc["character_limit"] = limit
                acc["character_count"] = used
                acc["character_remaining"] = rem
                acc["status"] = "active" if rem > 200 else "depleted"
                acc["last_checked"] = datetime.now().isoformat()
                self.save_accounts()
                return {"success": True, "account": acc}
            elif res.status_code == 401:
                acc["status"] = "invalid"
                acc["character_remaining"] = 0
                acc["last_checked"] = datetime.now().isoformat()
                self.save_accounts()
                return {"success": False, "error": "Invalid API Key or Unofficial Access disabled"}
            elif res.status_code == 429:
                acc["status"] = "rate_limited"
                acc["last_checked"] = datetime.now().isoformat()
                self.save_accounts()
                return {"success": False, "error": "Rate limited"}
            else:
                acc["status"] = f"error_{res.status_code}"
                acc["last_checked"] = datetime.now().isoformat()
                self.save_accounts()
                return {"success": False, "error": res.text}
        except Exception as e:
            acc["status"] = "network_error"
            acc["last_checked"] = datetime.now().isoformat()
            self.save_accounts()
            return {"success": False, "error": str(e)}

    def check_all_health(self) -> List[Dict[str, Any]]:
        """Verify health and remaining characters across all keys in pool."""
        results = []
        for acc in self.data["accounts"]:
            res = self.check_single_health(acc["id"])
            results.append(acc)
        return results

    def get_best_key(self, min_chars: int = 100) -> Optional[Dict[str, Any]]:
        """
        Smart load balancer: picks the active key with the highest remaining characters.
        If all active keys are below min_chars, falls back to any active key.
        """
        active_accounts = [
            a for a in self.data["accounts"]
            if a.get("status") in ("active", "unverified") and a.get("character_remaining", 10000) >= min_chars
        ]
        if not active_accounts:
            # Fallback to any active account
            active_accounts = [
                a for a in self.data["accounts"]
                if a.get("status") in ("active", "unverified") and a.get("character_remaining", 0) > 0
            ]
        if not active_accounts:
            return None
        
        # Sort by character_remaining descending
        active_accounts.sort(key=lambda x: x.get("character_remaining", 0), reverse=True)
        return active_accounts[0]

    def mark_key_failed(self, api_key: str, reason: str = "failed") -> None:
        """Mark a key as locked/depleted/rate limited on failure."""
        for acc in self.data["accounts"]:
            if acc["api_key"] == api_key:
                if "401" in reason or "invalid" in reason.lower():
                    acc["status"] = "locked"
                    acc["character_remaining"] = 0
                elif "429" in reason or "rate" in reason.lower():
                    acc["status"] = "rate_limited"
                else:
                    acc["status"] = "depleted"
                    acc["character_remaining"] = 0
                acc["last_checked"] = datetime.now().isoformat()
                break
        self.save_accounts()

    def record_usage(self, api_key: str, chars_used: int) -> None:
        """Deduct used characters in local tracker."""
        for acc in self.data["accounts"]:
            if acc["api_key"] == api_key:
                acc["character_count"] = acc.get("character_count", 0) + chars_used
                acc["character_remaining"] = max(0, acc.get("character_remaining", 10000) - chars_used)
                if acc["character_remaining"] <= 100:
                    acc["status"] = "depleted"
                break
        self.save_accounts()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary stats for dashboard header."""
        total = len(self.data["accounts"])
        active = sum(1 for a in self.data["accounts"] if a.get("status") == "active" or (a.get("status") == "unverified" and a.get("character_remaining", 0) > 0))
        total_remaining = sum(a.get("character_remaining", 0) for a in self.data["accounts"] if a.get("status") in ("active", "unverified"))
        return {
            "total_keys": total,
            "active_keys": active,
            "total_remaining_chars": total_remaining
        }

# Real-time user quota verification

# Highest-quota-first load balancer
