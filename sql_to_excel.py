import pandas as pd
import pymysql

# Creating a connection to SQL Database
connection = pymysql.connect(host='localhost', user='root', database='buy_plastic_db', password='actowiz', charset='utf8mb4', autocommit=True)
if connection.open:
    print('Database connection Successful!')
else:
    print('Database connection Un-Successful.')
cursor = connection.cursor()  # Creating a cursor to execute SQL Queries

query = '''SELECT * FROM prod_data;'''  # Query that will retrieve all data from Database table

data_frame = pd.read_sql(sql=query, con=connection)  # Reading Data from Database table and converting into DataFrame

data_frame.to_excel('buy_plastic_excel.xlsx')  # Converting DataFrame into Excel file
