FROM ubuntu:20.04

RUN apt-get update -y
RUN apt-get install -y python3.9
RUN apt update && apt install python3-pip -y
COPY requirements.txt /
RUN pip install -r /requirements.txt
RUN apt-get update && apt-get install -y gnupg
RUN apt-get install -y ca-certificates wget 

ENV conn_str=DefaultEndpointsProtocol=https;AccountName=synapsemetadata;AccountKey=I+AkJ4ktd6HjpRtSv1sxv5TIleIUk1OQYHhCqfK0430iHI4zM/7Z8QmuV/Ltj6yJYNNXnSLG4vhaPWfHc4/LaA==;EndpointSuffix=core.windows.net \
    container=default \
    PGPKeySecretName=Cantire-SFTP-PGP-Key \
    PGPKeyPasswordSecretName=Cantire-PGP-Decryption-Password \
    key_vault_name=Decryption-Keys \
    client_id=d403ef20-20ac-4334-b6de-6467b4a51bcc \
    tenant_id=152e5724-295e-4541-8b3b-9b6ce1a31927 \
    client_secret=5A3yLr3l07vR-q_kUPx86aIQG.HuZz._AV \
    SqlHostname='stg-discover-dollar.database.windows.net' \
    DB_Name='stg-etl-database' \
    SQLUsername='tushar' \
    SQLPassword='Lakhotia@123' \
    port=3306 \
    APPINSIGHTS_INSTRUMENTATIONKEY="37f4abe0-f484-42df-b992-c6de138207bc"
    
COPY . /home/site/wwwroot

WORKDIR /home/site/wwwroot

CMD ["python3","app.py"]