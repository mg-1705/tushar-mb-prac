import os
from zipfile import ZipFile
from io import BytesIO
import gzip
from KeyVault import KeyVault
from flask import current_app
import gnupg

class ProcessFile :
  def __init__(self) -> None:
    self.container=os.environ.get("container")
    try:
      vault = KeyVault()
      self.pgp_key=vault._fetchSecret(os.environ.get("PGPKeySecretName"))
      self.pgp_password=vault._fetchSecret(os.environ.get("PGPKeyPasswordSecretName"))
      # self.sqlUsername = vault.fetchSecret(os.environ.get("sqlusername"))
      # self.Sqlpassword = vault._fetchSecret(os.environ.get("sqlpassword"))
    except Exception as e:
      current_app.logger.info("Initialization did not happen successfully")
      current_app.logger.error(str(e))
    
  def createfile(self,blob_service_client,file,outputpath):
    '''
      Creata a BLOB file at the given path in the given container
    '''
    try :
      blob_client = blob_service_client.get_blob_client(self.container,outputpath)
      blob_client.upload_blob(file)
      current_app.logger.info(f"Successfully created a file at {outputpath}")
    except Exception as e:
      if "BlobAlreadyExists" in str(e):
        blob_client = blob_service_client.get_blob_client(self.container,f"{outputpath}/Files_with_same_name/")
        blob_client.upload_blob(file)
        current_app.logger.warn('Blob with the same name already exists' + outputpath + str(e))
      else :
        current_app.logger.error(f'Unable to write to destination folder {outputpath} ' + str(e))


  def decompress(self,blob_service_client,processed_directory,failure_directory,name,compressedFile):
    '''
        Uncompresses a given file using Gunzip/Unzip
    '''
    try:
      if name.endswith(".zip") :
          with ZipFile(BytesIO(compressedFile)) as zip_ref:
            for file_name in zip_ref.namelist():
                file_data = zip_ref.read(file_name)
                outputpath =f"{processed_directory}/{file_name}"
                self.createfile(blob_service_client,file_data,outputpath)
                current_app.logger.info(f"Successfully decompressed {name} into {outputpath}")
            return True

      elif name.endswith(".gz"):
          with gzip.open(BytesIO(compressedFile), 'rb') as gzip_file:
            file_data = gzip_file.read()
            outputpath =f"{processed_directory}/{name.replace('.gz','').replace('.gpg','')}"
            self.createfile(blob_service_client,file_data,outputpath)
            current_app.logger.info(f"Successfully decompressed {name} into {outputpath}")
          return True  
      
    except Exception as e:
      outputpath = f"{failure_directory}/{name}"
      self.createfile(blob_service_client,compressedFile,outputpath)    
      current_app.logger.error(f"Decompression failed for {name}. " + str(e) + "Saved a copy to Failure Bucket at "+ outputpath)
      return False                    
  
  def decrypt(self,blob_service_client,decrypted_directory,staging_directory,failure_directory,name,encryptedFile):
    '''
        Decrypts a given file using GPG/PGP
    '''
    try:
        gpg = gnupg.GPG(gpgbinary='/usr/bin/gpg')
        gpg.encoding = 'utf-8'
        newkey = self.pgp_key.split(" ")
        final_key =" ".join(newkey[0:5]) + "\n" + "\n".join(newkey[8:-5]) + "\n" + " ".join(newkey[-5:])
        import_result = gpg.import_keys(final_key)
        if import_result is None :
           current_app.logger.error("Importing of encryption keys failed")
        decrypted_data = gpg.decrypt(encryptedFile, passphrase=self.pgp_password)

        if not decrypted_data.ok:
          outputpath = f"{failure_directory}/{name}"
          self.createfile(blob_service_client,encryptedFile,outputpath)
          return (False,outputpath)
        else :
          outputpath = f"{decrypted_directory}/{name.replace('.gpg','')}"
          stagingpath = f"{staging_directory}/{name.replace('.gpg','')}"
          self.createfile(blob_service_client,decrypted_data.data,outputpath)
          self.createfile(blob_service_client,decrypted_data.data,stagingpath)
          return (decrypted_data.data,outputpath)
    
    except Exception as e:
        outputpath = f"{failure_directory}/{name}"
        self.createfile(blob_service_client,encryptedFile,outputpath)
        current_app.logger.error(f"decryption Failure file stored at {outputpath} " + str(e))
        return (False,outputpath)