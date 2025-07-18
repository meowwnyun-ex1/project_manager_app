import pyodbc

print("Available ODBC drivers:")
for driver in pyodbc.drivers():
    if "SQL Server" in driver:
        print(f"✅ {driver}")
