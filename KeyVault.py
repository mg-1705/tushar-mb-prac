import os
from azure.keyvault.secrets import SecretClient
from azure.identity import ClientSecretCredential
from flask import current_app

class KeyVault :
    def __init__(self):
        try:
            key_vault_name = os.environ.get('key_vault_name')
            client_id = os.environ.get("client_id")
            client_secret = os.environ.get("client_secret")
            tenant_id = os.environ.get("tenant_id")
            credential = ClientSecretCredential(tenant_id=tenant_id,client_id=client_id,client_secret=client_secret)
            self.client = SecretClient(vault_url=f"https://{key_vault_name}.vault.azure.net/", credential=credential)  
        except Exception as e:
            current_app.logger.error("Unable to initialize Azure Key Vault." + str(e))

    def _fetchSecret(self,secretName):
        '''
        Fetches a given secret value from a configured Key Vault using a Secret Name
        
        Caller has to pass Secret Name.
        '''
        try:
            current_app.logger.info(f'Fetching Secret {secretName} from Azure KeyVault...')
            secret  =  self.client.get_secret(secretName).value
            if (secret):
                  current_app.logger.info(f'Successfully retrieved secret {secretName} from Azure Key Vault.')
            return secret
        except Exception as e:
            current_app.logger.error(f'Unable to fetch secret {secretName} from Azure Key Vault. No secret was returned!' + str(e))
