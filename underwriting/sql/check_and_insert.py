import oracledb

conn = oracledb.connect(
    user='ifsapp',
    password='sn1974',
    dsn='192.168.48.17:1521/TEST'
)
cur = conn.cursor()

# Tablo yapisi
cur.execute(
    "SELECT column_name, data_type, data_length, nullable "
    "FROM all_tab_columns WHERE table_name = 'TRLEAS_USERS_TAB' "
    "ORDER BY column_id"
)
print('=== TRLEAS_USERS_TAB COLUMNS ===')
for row in cur.fetchall():
    print(row)

# Mevcut kayitlar
cur.execute('SELECT * FROM TRLEAS_USERS_TAB FETCH FIRST 5 ROWS ONLY')
cols = [d[0] for d in cur.description]
print()
print('COLUMNS:', cols)
print('=== SAMPLE ROWS ===')
for row in cur.fetchall():
    print(row)

# Grant tablosu yapisi
cur.execute(
    "SELECT column_name, data_type, data_length, nullable "
    "FROM all_tab_columns WHERE table_name = 'TRLEAS_USER_GRANT_TAB' "
    "ORDER BY column_id"
)
print()
print('=== TRLEAS_USER_GRANT_TAB COLUMNS ===')
for row in cur.fetchall():
    print(row)

# tarik.corut kullanicisinin grant kayitlari
cur.execute(
    "SELECT * FROM TRLEAS_USER_GRANT_TAB WHERE identity = 'tarik.corut'"
)
gcols = [d[0] for d in cur.description]
print()
print('GRANT COLUMNS:', gcols)
print('=== tarik.corut GRANT ROWS ===')
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()
