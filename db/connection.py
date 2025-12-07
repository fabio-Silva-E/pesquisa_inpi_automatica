import pyodbc


def conectar_banco():
    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=192.168.3.121,1433;"
            "DATABASE=INPI_Busca;"
            "UID=admin;"
            "PWD=24098675"
        )
        return conn
    except Exception as e:
        print("❌ Erro ao conectar no SQL Server:", e)
        return None
