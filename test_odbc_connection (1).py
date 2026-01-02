"""
ODBC Connection Test Script for Sports Management System
Run this script to diagnose and fix any ODBC connection issues
"""

import os
import sys
import pyodbc
import platform

def print_system_info():
    """Print system information for debugging"""
    print("\n=== SYSTEM INFORMATION ===")
    print(f"Platform: {platform.platform()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Architecture: {'64-bit' if sys.maxsize > 2**32 else '32-bit'}")
    print(f"Current Directory: {os.getcwd()}")

def print_available_drivers():
    """Print all available ODBC drivers"""
    print("\n=== AVAILABLE ODBC DRIVERS ===")
    drivers = pyodbc.drivers()
    
    if not drivers:
        print("No ODBC drivers found. Please install the required drivers.")
        return False
    
    print("Installed ODBC Drivers:")
    for i, driver in enumerate(drivers, 1):
        print(f"{i}. {driver}")
    
    access_drivers = [x for x in drivers if 'Access' in x]
    if not access_drivers:
        print("\nNo Microsoft Access drivers found. Please install the Microsoft Access Database Engine.")
        return False
    else:
        print("\nMicrosoft Access Drivers:")
        for driver in access_drivers:
            print(f"- {driver}")
        return True

def test_database_connection(db_path, driver=None):
    """Test connection to the specified database with the specified driver"""
    print(f"\n=== TESTING CONNECTION TO DATABASE ===")
    print(f"Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file does not exist at {db_path}")
        return False
    
    if not driver:
        # Try to find an Access driver
        drivers = [x for x in pyodbc.drivers() if 'Access' in x]
        if not drivers:
            print("ERROR: No Microsoft Access drivers found")
            return False
        driver = drivers[0]
    
    print(f"Using driver: {driver}")
    
    try:
        conn_str = f"DRIVER={{{driver}}};DBQ={db_path};"
        print(f"Connection string: {conn_str}")
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get table names for verification
        tables = []
        for row in cursor.tables():
            if row.table_type == 'TABLE':
                tables.append(row.table_name)
        
        print("Connection successful!")
        print(f"Tables found in database: {tables}")
        
        if 'USERS' in tables:
            cursor.execute("SELECT COUNT(*) FROM USERS")
            user_count = cursor.fetchone()[0]
            print(f"Number of users in database: {user_count}")
        
        conn.close()
        return True
    
    except pyodbc.Error as e:
        print(f"ERROR: {str(e)}")
        return False

def try_alternative_connections(db_path):
    """Try different drivers and connection methods"""
    print("\n=== TRYING ALTERNATIVE CONNECTION METHODS ===")
    
    access_drivers = [x for x in pyodbc.drivers() if 'Access' in x]
    success = False
    
    for driver in access_drivers:
        print(f"\nTrying driver: {driver}")
        try:
            conn_str = f"DRIVER={{{driver}}};DBQ={db_path};"
            print(f"Connection string: {conn_str}")
            
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            print(f"SUCCESS: Connection worked with {driver}")
            success = True
            break
        except pyodbc.Error as e:
            print(f"FAILED: {str(e)}")
    
    if not success:
        print("\nTrying DSN-less connection...")
        try:
            # Another method for older systems
            conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={db_path};"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            print("SUCCESS: DSN-less connection worked")
            success = True
        except pyodbc.Error as e:
            print(f"FAILED: {str(e)}")
    
    return success

def suggest_fixes():
    """Suggest fixes for common issues"""
    print("\n=== SUGGESTED FIXES ===")
    print("1. Make sure you have the Microsoft Access Database Engine installed:")
    print("   - Download link: https://www.microsoft.com/en-us/download/details.aspx?id=54920")
    print("   - Install the version that matches your Python architecture (32-bit or 64-bit)")
    
    print("\n2. Check if the database path is correct and accessible")
    
    print("\n3. Try using a full, absolute path to your database file")
    
    print("\n4. If using 64-bit Python, consider switching to 32-bit Python if you have 32-bit Office installed")
    
    print("\n5. Ensure you have proper read/write permissions to the database file")

def main():
    """Main test function"""
    print("=== SPORTS MANAGEMENT SYSTEM DATABASE CONNECTION TEST ===")
    
    # Print system information
    print_system_info()
    
    # Check for available drivers
    drivers_available = print_available_drivers()
    if not drivers_available:
        print("\nCritical issue: No Microsoft Access drivers found.")
        suggest_fixes()
        return
    
    # Get database path
    default_path = os.path.join(os.getcwd(), 'sports_management_system.accdb')
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = input(f"\nEnter the path to your database file [default: {default_path}]: ")
        if not db_path:
            db_path = default_path
    
    # Normalize path
    db_path = os.path.normpath(db_path)
    
    # Test the connection
    success = test_database_connection(db_path)
    
    if not success:
        print("\nTrying alternative connection methods...")
        success = try_alternative_connections(db_path)
    
    if not success:
        print("\nAll connection attempts failed.")
        suggest_fixes()
    else:
        print("\n=== CONNECTION TEST COMPLETED SUCCESSFULLY ===")
        print("Your ODBC connection to Microsoft Access is working properly.")
        print("\nTo use this connection in your app, use the following code:")
        print("\nimport pyodbc")
        print("def get_db_connection():")
        print(f"    conn_str = r'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};'")
        print("    return pyodbc.connect(conn_str)")
        print("\n# Example usage:")
        print("# conn = get_db_connection()")
        print("# cursor = conn.cursor()")
        print("# cursor.execute('SELECT * FROM USERS')")
        print("# rows = cursor.fetchall()")
        print("# conn.close()")

if __name__ == "__main__":
    main()