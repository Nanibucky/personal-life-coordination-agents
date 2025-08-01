"""
Helper Utilities
Common utility functions used across the project
"""

import json
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import asyncio
import aiohttp
from pathlib import Path

def generate_id(prefix: str = "") -> str:
    """Generate a unique ID"""
    unique_id = str(uuid.uuid4()).replace("-", "")[:12]
    return f"{prefix}{unique_id}" if prefix else unique_id

def hash_string(text: str) -> str:
    """Generate SHA-256 hash of a string"""
    return hashlib.sha256(text.encode()).hexdigest()

def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON string"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "") -> str:
    """Safely serialize object to JSON string"""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def format_file_size(bytes_size: int) -> str:
    """Format file size in bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + ('.' + ext if ext else '')
    return filename or 'unnamed'

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

async def retry_async(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Retry an async function with exponential backoff"""
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                await asyncio.sleep(delay * (backoff ** attempt))
            else:
                raise last_exception

async def make_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """Make HTTP request with error handling"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.request(method, url, headers=headers, json=data) as response:
                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "data": await response.json() if response.content_type == "application/json" else await response.text(),
                    "success": 200 <= response.status < 300
                }
    except Exception as e:
        return {
            "status": 0,
            "headers": {},
            "data": None,
            "success": False,
            "error": str(e)
        }

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    import re
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Check if it's a valid length (7-15 digits)
    return 7 <= len(digits_only) <= 15

def parse_datetime(date_string: str, formats: Optional[List[str]] = None) -> Optional[datetime]:
    """Parse datetime string with multiple format support"""
    if formats is None:
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y"
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    return None

def get_relative_time(dt: datetime) -> str:
    """Get human readable relative time"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "just now"

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text"""
    import re
    from collections import Counter
    
    # Remove special characters and convert to lowercase
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count word frequencies
    word_counts = Counter(words)
    
    # Return most common words
    return [word for word, count in word_counts.most_common(max_keywords)]
