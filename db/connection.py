import pyodbc


def conectar_banco():
    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost\\SQLEXPRESS;"
            "DATABASE=INPI_Busca;"
            "Trusted_Connection=yes;"
        )
        return conn
    except Exception as e:
        print("❌ Erro ao conectar no SQL Server:", e)
        return None
