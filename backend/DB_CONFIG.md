# Database Configuration for Smart Waste Management System

## MySQL Configuration

### Connection Pool Settings
```python
# Recommended settings for production
MYSQL_POOL_SIZE = 10
MYSQL_POOL_NAME = "swms_pool"
MYSQL_POOL_RESET_SESSION = True
```

### Connection Parameters
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'waste_management',
    'pool_size': 10,
    'pool_name': 'swms_pool',
    'autocommit': True,
    'raise_on_warnings': True
}
```

## Connection Pooling Benefits
1. **Performance**: Reuse existing connections instead of creating new ones
2. **Resource Management**: Limit the number of concurrent database connections
3. **Scalability**: Handle multiple requests efficiently
4. **Reliability**: Automatic connection recovery

## Usage Example
```python
import mysql.connector
from mysql.connector import pooling

# Create connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="swms_pool",
    pool_size=10,
    pool_reset_session=True,
    **DB_CONFIG
)

# Get connection from pool
connection = connection_pool.get_connection()
cursor = connection.cursor()

# Execute queries
cursor.execute("SELECT * FROM bins")
results = cursor.fetchall()

# Return connection to pool
cursor.close()
connection.close()
```

## Environment Variables
Set these in your .env file:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=waste_management
DB_POOL_SIZE=10
```

## Best Practices
- Always close connections after use
- Use context managers for automatic cleanup
- Set appropriate pool size based on application load
- Monitor connection pool usage
- Implement connection timeout handling
