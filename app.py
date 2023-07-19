from flask import Flask,request
from applicationinsights.flask.ext import AppInsights
from azure.storage.blob import BlobServiceClient
from MetaData import Metadata
from ProcessFile import ProcessFile
from datetime import datetime
import pytz 
import logging
import os

app = Flask(__name__)
app.config['APPINSIGHTS_INSTRUMENTATIONKEY'] = os.environ.get("APPINSIGHTS_INSTRUMENTATIONKEY")
insights = AppInsights(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/", methods=['get'])
def index():
    date_format = "%Y-%m-%dT%H:%M:%S"
    file_name = request.args.get('file')
    encrypted_directory = request.args.get('raw_source_folder')
    decrypted_directory  = request.args.get('raw_decrypted_folder')
    archive_directory = request.args.get('raw_archive_folder')
    decryption_failure_directory = request.args.get('raw_decryption_failure_folder')
    decompress_failure_directory = request.args.get("raw_decompress_failure_folder")
    staging_directory = request.args.get('raw_stage_folder')
    processed_directory =  request.args.get('raw_write_folder')
    last_process_date = request.args.get("last_scan_time")
    last_process_date = datetime.strptime(last_process_date, date_format)
    app.logger.info("Process Started ...")
    process_file = ProcessFile()
    metadata = Metadata()
    try:
        metadata.details['pre_process_scan_start_time'] = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
        conn_str=os.environ.get("conn_str")
        container=os.environ.get("container")
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        container_client = blob_service_client.get_container_client(container)
        directories = container_client.walk_blobs(name_starts_with=f"{encrypted_directory}")
        for directory in directories:
            directory_name = directory["name"]
            blob_list = container_client.list_blobs(name_starts_with=f"{directory_name}{file_name}",include="Metadata")
            for blob in blob_list :
                date_convertable = blob.last_modified
                timezone_ist = pytz.timezone('Asia/Kolkata')
                date_ist = date_convertable.astimezone(timezone_ist)
                last_modified = date_ist.replace(tzinfo=None)
                if last_modified >= last_process_date :
                    app.logger.info(f"Processing file {blob.name} ...")  
                    name = blob.name.split("/")[-1]    
                    blob_client = container_client.get_blob_client(blob.name)
                    file = blob_client.download_blob().readall()
                    decryptedFile , decryptedFile_Path = process_file.decrypt(blob_service_client,decrypted_directory,staging_directory,decryption_failure_directory,name,file)
                    decrypted_File_Name = name.replace('.gpg','')
                    if not decryptedFile :
                        app.logger.error(f"decryption Failure file stored at {decryptedFile_Path}")
                        blob_client.delete_blob()
                    else :
                        compression = process_file.decompress(blob_service_client,processed_directory,decompress_failure_directory,decrypted_File_Name,decryptedFile)
                        if compression :
                            archive_path =f"{archive_directory}/{name}"
                            process_file.createfile(blob_service_client,file,archive_path)
                            blob_client.delete_blob()   
                            # metadata.details['Decrypted'] = 1
                        else :    
                            blob_client.delete_blob()    
                            app.logger.error(f"Compression failure")  
        metadata.details['pre_process_scan_end_time'] = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
        metadata.write(file_name)   

    except Exception as e:
        app.logger.error("An error occured. "+str(e))
        metadata.conn_close()
        return("This function did not executed successfully.") 
    
    app.logger.info("This app excecuted successfully")
    metadata.conn_close()
    return("This function executed successfully.")    

if __name__=='__main__':
     app.run(host='0.0.0.0')
