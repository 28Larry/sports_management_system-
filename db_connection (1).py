"""
Database connection module for Sports Management System
Provides robust connection handling for Microsoft Access database via pyodbc
"""

import os
import pyodbc
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    filename='database.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database')

class DatabaseConnection:
    """Class to handle database connections to Microsoft Access"""
    
    def __init__(self, db_path=None):
        """Initialize with database path or use default"""
        if db_path:
            self.db_path = db_path
        else:
            # Use the default path relative to the project root
            root_dir = Path(__file__).parent  # Assumes this file is in the project root
            self.db_path = os.path.join(root_dir, 'sports_management_system.accdb')
        
        # Normalize path for Windows
        self.db_path = os.path.normpath(self.db_path)
        logger.info(f"Database path set to: {self.db_path}")
        
        # Verify database file exists
        if not os.path.exists(self.db_path):
            logger.error(f"Database file not found at {self.db_path}")
            raise FileNotFoundError(f"Database file not found at {self.db_path}")
    
    def get_connection(self):
        """Get a connection to the database"""
        try:
            # List available drivers for debugging
            drivers = [x for x in pyodbc.drivers() if x.startswith('Microsoft Access')]
            if not drivers:
                logger.error("No Microsoft Access ODBC drivers found")
                raise Exception("No Microsoft Access ODBC drivers found. Please install the Microsoft Access Database Engine.")
            
            logger.info(f"Available drivers: {drivers}")
            driver = drivers[0]  # Use the first available driver
            
            # Create connection string
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"DBQ={self.db_path};"
            )
            
            # Connect to the database
            conn = pyodbc.connect(conn_str)
            logger.info("Database connection established successfully")
            return conn
        
        except pyodbc.Error as e:
            logger.error(f"Execute many error: {str(e)}")
            if conn:
                conn.rollback()
            raise
        
        finally:
            if conn:
                conn.close()


# Global database connection instance
db = DatabaseConnection()


def get_db_connection():
    """Function to get a database connection (for backward compatibility)"""
    return db.get_connection()


if __name__ == "__main__":
    # Test the connection if this file is run directly
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get table names for verification
        tables = []
        for row in cursor.tables():
            if row.table_type == 'TABLE':
                tables.append(row.table_name)
        
        print("Connection successful!")
        print(f"Available tables: {tables}")
        
        conn.close()
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}")
        raise
    
    def execute_query(self, query, params=None, fetchall=True):
        """Execute a query and return the results"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetchall:
                results = cursor.fetchall()
                return results
            else:
                conn.commit()
                return cursor.rowcount
        
        except pyodbc.Error as e:
            logger.error(f"Query execution error: {str(e)}")
            if conn:
                conn.rollback()
            raise
        
        finally:
            if conn:
                conn.close()
    
    def execute_many(self, query, params_list):
        """Execute multiple queries with different parameters"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        
        except pyodbc.Error as e:
            logger.error("An error occurred while executing multiple queries.")