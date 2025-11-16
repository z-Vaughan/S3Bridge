# API Reference - Universal S3 Library

Complete API documentation for the Universal S3 Library.

## UniversalS3Client

Main client class for S3 operations with automatic credential management.

### Constructor

```python
UniversalS3Client(bucket_name: str, service_name: str)
```

**Parameters:**
- `bucket_name` (str): S3 bucket name to access
- `service_name` (str): Service identifier for permissions

**Example:**
```python
from universal_s3_library import UniversalS3Client

client = UniversalS3Client("my-app-data", "webapp")
```

### File Operations

#### file_exists(key: str) -> bool

Check if a file exists in the bucket.

```python
exists = client.file_exists("config/settings.json")
if exists:
    print("Configuration file found")
```

#### upload_file(local_path: str, key: str) -> bool

Upload a local file to S3.

```python
success = client.upload_file("backup.zip", "backups/daily.zip")
if success:
    print("File uploaded successfully")
```

#### download_file(key: str, local_path: str) -> bool

Download a file from S3 to local filesystem.

```python
success = client.download_file("data.csv", "local_data.csv")
if success:
    print("File downloaded successfully")
```

### JSON Operations

#### read_json(key: str) -> Optional[Dict[str, Any]]

Read and parse a JSON file from S3.

```python
config = client.read_json("config/app_settings.json")
if config:
    database_url = config.get("database_url")
```

#### write_json(data: Dict[str, Any], key: str) -> bool

Write data as JSON to S3.

```python
config = {
    "database_url": "localhost:5432",
    "debug": True,
    "features": ["auth", "logging"]
}
success = client.write_json(config, "config/app_settings.json")
```

### Text Operations

#### read_text(key: str) -> Optional[str]

Read a text file from S3.

```python
log_content = client.read_text("logs/application.log")
if log_content:
    lines = log_content.split('\n')
    print(f"Log has {len(lines)} lines")
```

#### write_text(content: str, key: str) -> bool

Write text content to S3.

```python
log_entry = "2024-01-01 12:00:00 - Application started\n"
success = client.write_text(log_entry, "logs/app.log")
```

### Listing and Management

#### list_objects(prefix: str = "") -> List[str]

List objects in bucket with optional prefix filter.

```python
# List all objects
all_objects = client.list_objects()

# List objects with prefix
reports = client.list_objects("reports/")
configs = client.list_objects("config/")

print(f"Found {len(reports)} reports")
```

#### delete_object(key: str) -> bool

Delete an object from S3.

```python
success = client.delete_object("temp/old_file.txt")
if success:
    print("File deleted successfully")
```

## UniversalAuthProvider

Authentication provider for managing AWS credentials.

### Constructor

```python
UniversalAuthProvider(service_name: str = "default")
```

**Parameters:**
- `service_name` (str): Service identifier for credential requests

### Methods

#### get_credentials() -> Dict[str, Any]

Get current AWS credentials (with automatic refresh).

```python
from universal_s3_library import UniversalAuthProvider

auth = UniversalAuthProvider("webapp")
creds = auth.get_credentials()

# Returns:
# {
#     'access_key': 'AKIA...',
#     'secret_key': 'abc123...',
#     'session_token': 'IQoJ...'
# }
```

#### credentials_expired() -> bool

Check if cached credentials are expired.

```python
if auth.credentials_expired():
    print("Credentials need refresh")
```

#### invalidate_credentials()

Force refresh of cached credentials on next request.

```python
auth.invalidate_credentials()
# Next get_credentials() call will fetch fresh credentials
```

#### reset_authentication()

Reset authentication state (clears cache).

```python
auth.reset_authentication()
```

## Error Handling

### Common Exceptions

```python
from universal_s3_library import UniversalS3Client

try:
    client = UniversalS3Client("restricted-bucket", "analytics")
    data = client.read_json("sensitive/data.json")
except ValueError as e:
    # Bucket access validation errors
    if "not authorized" in str(e):
        print("Service not authorized for this bucket")
    else:
        print(f"Configuration error: {e}")
except Exception as e:
    # S3 operation errors
    print(f"S3 operation failed: {e}")
```

### Error Types

- `ValueError`: Service/bucket validation errors
- `Exception`: Network, S3, or credential errors

## Usage Patterns

### Configuration Management

```python
class AppConfig:
    def __init__(self, bucket_name: str, service_name: str):
        self.client = UniversalS3Client(bucket_name, service_name)
        self.config_key = "config/app.json"
    
    def load_config(self) -> dict:
        return self.client.read_json(self.config_key) or {}
    
    def save_config(self, config: dict) -> bool:
        return self.client.write_json(config, self.config_key)
    
    def get_setting(self, key: str, default=None):
        config = self.load_config()
        return config.get(key, default)

# Usage
config = AppConfig("myapp-config", "webapp")
db_url = config.get_setting("database_url", "localhost:5432")
```

### Batch Operations

```python
def process_files(client: UniversalS3Client, prefix: str):
    """Process all files with given prefix"""
    files = client.list_objects(prefix)
    
    for file_key in files:
        if file_key.endswith('.json'):
            data = client.read_json(file_key)
            if data:
                # Process JSON data
                processed = transform_data(data)
                
                # Save processed version
                output_key = file_key.replace('.json', '_processed.json')
                client.write_json(processed, output_key)

# Usage
client = UniversalS3Client("data-bucket", "processor")
process_files(client, "input/")
```

### Async Operations

```python
import asyncio
import concurrent.futures
from typing import List

async def upload_files_async(client: UniversalS3Client, files: List[tuple]):
    """Upload multiple files concurrently"""
    loop = asyncio.get_event_loop()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [
            loop.run_in_executor(executor, client.upload_file, local_path, s3_key)
            for local_path, s3_key in files
        ]
        
        results = await asyncio.gather(*tasks)
        return results

# Usage
files_to_upload = [
    ("local1.txt", "uploads/file1.txt"),
    ("local2.txt", "uploads/file2.txt"),
    ("local3.txt", "uploads/file3.txt")
]

client = UniversalS3Client("upload-bucket", "uploader")
results = asyncio.run(upload_files_async(client, files_to_upload))
print(f"Uploaded {sum(results)} files successfully")
```

## Environment Configuration

### API Key Setup

```python
import os

# Set via environment variable
os.environ['UNIVERSAL_S3_API_KEY'] = 'your-api-key-here'

# Or load from config file
def load_api_key():
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('UNIVERSAL_S3_API_KEY='):
                    return line.split('=', 1)[1].strip()
    except FileNotFoundError:
        pass
    return None

if not os.environ.get('UNIVERSAL_S3_API_KEY'):
    api_key = load_api_key()
    if api_key:
        os.environ['UNIVERSAL_S3_API_KEY'] = api_key
```

### Service Configuration

```python
# Development
dev_client = UniversalS3Client("myapp-dev-data", "myapp-dev")

# Staging  
staging_client = UniversalS3Client("myapp-staging-data", "myapp-staging")

# Production
prod_client = UniversalS3Client("myapp-prod-data", "myapp-prod")
```

## Performance Considerations

### Credential Caching

Credentials are automatically cached and refreshed:
- Cache duration: ~50 minutes (10 minutes before expiry)
- Automatic refresh on expiration
- Thread-safe credential management

### Large File Handling

```python
# For large files, use download_file instead of read_text
client = UniversalS3Client("large-data", "processor")

# Good: Downloads to local file
client.download_file("large_dataset.csv", "local_dataset.csv")

# Avoid: Loads entire file into memory
# content = client.read_text("large_dataset.csv")  # Don't do this
```

### Batch Operations

```python
# Efficient: Single list operation
files = client.list_objects("data/")
for file_key in files:
    if file_key.endswith('.json'):
        process_file(client, file_key)

# Inefficient: Multiple existence checks
# for i in range(1000):
#     if client.file_exists(f"data/file_{i}.json"):  # Don't do this
#         process_file(client, f"data/file_{i}.json")
```