import mysql.connector
import os 
import pymssql
from flask import current_app

class Metadata(): 

    def __init__(self) -> None:
        try:  
            current_app.logger.info("Initialization of Metadata table started")
            Hostname = os.environ.get('SqlHostname')
            DB_Name = os.environ.get('DB_Name')
            Username = os.environ.get('SQLUsername')
            Password = os.environ.get('SQLPassword')
            Port = os.environ.get('port')
            self.conn = pymssql.connect(server=Hostname,
                            user=Username,
                            password=Password,
                            database=DB_Name)
            
            self.cursor  = self.conn.cursor()
            self.details = {}
            current_app.logger.info("Initialization of Metadata table successfull")
        except Exception as e :
            current_app.logger.error("unable to connect to watermark table" + str(e))

    def write(self,file_name) :
       try:
        query = "UPDATE watermark_tbl SET " + ", ".join([f"{column} = '{value}'" for column, value in self.details.items()])
        query += f" WHERE file_name = '{file_name}'"
        self.cursor.execute(query)
        self.conn.commit()
       except Exception as e:
           current_app.logger.error("unable to update watermark table" + str(e)) 
        
    def conn_close(self):
        self.cursor.close()
        self.conn.close()

