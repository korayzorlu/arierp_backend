from django.test import TestCase

import pyodbc
import json



# Create your tests here.

SERVER = "192.168.81.7,1433"
DATABASE = "ARI_LEASING"
USERNAME = "koray.zorlu"
PASSWORD = "Kozo5313-*"

connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Provider=SQLNCLI11;Integrated Security=SSPI;Persist Security Info=False;Initial Catalog=MASTER;Data Source=VSRV2;TrustServerCertificate=yes;'

try:
    conn = pyodbc.connect(connectionString)
    
    SQL_QUERY = """
    SELECT TOP 1000 OperationProjectId,SequenceNo FROM LeasingOperationProject;
    """

    cursor = conn.cursor()
    cursor.execute(SQL_QUERY)
    
    records = cursor.fetchall()
    # for r in records:
        
    #     row_to_list = [elem for elem in r]
    external_data=[]
    for r in records:
        row_to_list = [elem for elem in r]
        
        external_data.append({
            "id" : id,
            "operationProjectId" : r.OperationProjectId,
            "sequenceNo" : r.SequenceNo,
        })
        
        id = id + 1
    print(external_data)
except Exception as e:
    print(e)


