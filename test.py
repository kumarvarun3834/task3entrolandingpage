import MySQLdb

conn = MySQLdb.connect(
    host="127.0.0.1",
    user="root",
    passwd="testcase",
    db="test_conn",
    port=3306
)
cursor = conn.cursor()
cursor.execute("SHOW TABLES;")
print(cursor.fetchall())
