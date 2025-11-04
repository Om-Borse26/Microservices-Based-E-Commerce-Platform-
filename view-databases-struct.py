import pymysql
import sys
from tabulate import tabulate

HOST = "shopease-mysql-db.cmni2wmcozyh.us-east-1.rds.amazonaws.com"
USER = "admin"
PASSWORD = "Yog101619Admin"
PORT = 3306

print("\n" + "="*100)
print(" "*35 + "SHOPEASE RDS DATABASE STRUCTURE")
print("="*100)

try:
    conn = pymysql.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        port=PORT,
        charset='utf8mb4',
        connect_timeout=30
    )
    
    cursor = conn.cursor()
    
    databases = ['productdb', 'userdb', 'orderdb', 'paymentdb', 'notificationdb']
    
    for db_name in databases:
        cursor.execute(f"USE {db_name}")
        
        print(f"\n{'='*100}")
        print(f"📦 DATABASE: {db_name.upper()}")
        print(f"{'='*100}")
        
        # Get all tables in database
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        for table_tuple in tables:
            table_name = table_tuple[0]
            
            print(f"\n┌{'─'*98}┐")
            print(f"│ 📋 TABLE: {table_name:<85} │")
            print(f"└{'─'*98}┘")
            
            # Get table structure
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            # Format column information
            column_data = []
            for col in columns:
                field = col[0]
                col_type = col[1]
                null = col[2]
                key = col[3]
                default = col[4] if col[4] is not None else 'NULL'
                extra = col[5]
                
                # Truncate long types
                if len(str(col_type)) > 30:
                    col_type = str(col_type)[:27] + "..."
                
                # Add emoji for key types
                key_icon = ""
                if key == "PRI":
                    key_icon = "🔑"
                elif key == "MUL":
                    key_icon = "🔗"
                elif key == "UNI":
                    key_icon = "⭐"
                
                column_data.append([
                    key_icon,
                    field,
                    col_type,
                    null,
                    default,
                    extra
                ])
            
            # Print table using tabulate
            headers = ["Key", "Column Name", "Data Type", "Null", "Default", "Extra"]
            print(tabulate(column_data, headers=headers, tablefmt="grid"))
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\n   📊 Total Rows: {count}")
            
            # Get indexes
            cursor.execute(f"SHOW INDEX FROM {table_name}")
            indexes = cursor.fetchall()
            
            if indexes:
                print(f"\n   🔍 Indexes:")
                index_dict = {}
                for idx in indexes:
                    index_name = idx[2]
                    column_name = idx[4]
                    
                    if index_name not in index_dict:
                        index_dict[index_name] = []
                    index_dict[index_name].append(column_name)
                
                for idx_name, cols in index_dict.items():
                    cols_str = ", ".join(cols)
                    if idx_name == "PRIMARY":
                        print(f"      • PRIMARY KEY: ({cols_str})")
                    else:
                        print(f"      • {idx_name}: ({cols_str})")
            
            # Show sample data if available
            if count > 0 and count <= 10:
                print(f"\n   📄 Sample Data:")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_rows = cursor.fetchall()
                
                # Get column names
                cursor.execute(f"DESCRIBE {table_name}")
                col_info = cursor.fetchall()
                col_names = [col[0] for col in col_info]
                
                sample_data = []
                for row in sample_rows:
                    row_data = []
                    for val in row:
                        if val is None:
                            row_data.append("NULL")
                        elif isinstance(val, str) and len(val) > 30:
                            row_data.append(val[:27] + "...")
                        else:
                            row_data.append(str(val))
                    sample_data.append(row_data)
                
                print(tabulate(sample_data, headers=col_names, tablefmt="grid"))
    
    print("\n" + "="*100)
    print(" "*30 + "✅ DATABASE STRUCTURE DISPLAYED SUCCESSFULLY")
    print("="*100 + "\n")
    
    conn.close()
    
except ImportError:
    print("\n❌ Error: 'tabulate' module not found!")
    print("\n📦 Install it with:")
    print("   pip install tabulate\n")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)