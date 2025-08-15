# from pymilvus import connections, Collection

# # ---- Connection Details ----
# # Replace with your Milvus Cloud credentials
# MILVUS_URI="https://in03-b24fbf72fa83f44.serverless.gcp-us-west1.cloud.zilliz.com"
# MILVUS_TOKEN="cd56cdc1cd483caa402da6cc5846d5a2cbeb6e6ca1e9c99e718672027b4ef2fc51b43e507d1220a8ca89c2e199c922e0f86b539d"

# #MILVUS_URI = "https://your-milvus-instance.cloud.milvus.io"
# #TOKEN = "your-token-here"  # usually "username:password" for Milvus Cloud
# COLLECTION_NAME = "youtube_creator_videos"

# def connect_to_milvus():
#     # Connect to Milvus Cloud
#     connections.connect(
#         alias="default",
#         uri=MILVUS_URI,
#         token=MILVUS_TOKEN
#     )
#     print("✅ Connected to Milvus")

# def check_collection():
#     collection = Collection(name=COLLECTION_NAME)
#     print(f"📂 Collection: {COLLECTION_NAME}")
#     print(f"Total entities: {collection.num_entities}")
#     print(f"Schema: {collection.schema}")

# if __name__ == "__main__":
#     connect_to_milvus()
#     check_collection()

# # milvus_connect_test.py
# from pymilvus import connections, utility

# # Set these from your Zilliz/Milvus Cloud "Connect" panel (Python tab)
# MILVUS_URI = "https://in03-xxxxxxxxxxxxxxxx.serverless.gcp-us-west1.cloud.zilliz.com"
# MILVUS_TOKEN = "YOUR_API_KEY"   # exactly the API Key shown in the portal

# def main():
#     print("Connecting…")
#     connections.connect(
#         alias="default",
#         uri=MILVUS_URI,
#         token=MILVUS_TOKEN,
#     )
#     print("✅ Connected")

#     # Simple sanity checks
#     print("Server version:", utility.get_server_version())
#     print("Has connection:", connections.has_connection("default"))

#     # List collections to confirm access
#     print("Collections:", utility.list_collections())

# if __name__ == "__main__":
#     main()

#     curl -I https://in03-b24fbf72fa83f44.serverless.gcp-us-west1.cloud.zilliz.com


# milvus_cloud_connect.py
#from pymilvus import MilvusClient  # provided by pymilvus>=2.4

# import os, sys, textwrap

# URI="https://in03-b24fbf72fa83f44.serverless.gcp-us-west1.cloud.zilliz.com"
# TOKEN="cd56cdc1cd483caa402da6cc5846d5a2cbeb6e6ca1e9c99e718672027b4ef2fc51b43e507d1220a8ca89c2e199c922e0f86b539d"  # paste exactly as shown in console

# milvus_diag.py



# print("== Inputs ==")
# print("URI:", URI)
# print("URI len:", len(URI))
# print("TOKEN len:", len(TOKEN))
# print("TOKEN preview:", repr(TOKEN[:6]) + "…")  # repr shows hidden chars
# if TOKEN.strip() != TOKEN:
#     print("WARNING: TOKEN contains leading/trailing whitespace!")
# if "\n" in TOKEN or "\r" in TOKEN:
#     print("WARNING: TOKEN includes newline characters!")

# def step(name):
#     print("\n" + "="*10, name, "="*10)

# # 1) High-level client (milvus>=2.4)
# try:
#     step("High-level MilvusClient")
#     from milvus import MilvusClient  # pip install "pymilvus>=2.4.4" also provides this
#     client = MilvusClient(uri=URI, token=TOKEN, db_name="default", timeout=30)
#     print("Connected ✔")
#     print("Collections:", client.list_collections())
# except Exception as e:
#     print("High-level client failed:", repr(e))

# # 2) Lower-level client
# try:
#     step("Lower-level pymilvus")
#     from pymilvus import connections, utility, Collection
#     connections.connect(alias="default", uri=URI, token=TOKEN, db_name="default", timeout=30)
#     print("Connected ✔")
#     print("Server version:", utility.get_server_version())
#     print("Collections:", utility.list_collections())
# except Exception as e:
#     print("Lower-level client failed:", repr(e))

# 1) Activate your venv first
# macOS/Linux example:


# 2) Upgrade/downgrade to a compatible set
# pip install -U "pymilvus>=2.4.6" "grpcio>=1.58.0" "protobuf<6"

# If you still see protobuf warnings, force this exact pin:
# pip install "protobuf==5.27.2"

# 3) Try this minimal script
# python - <<'PY'
import logging
logging.basicConfig(level=logging.INFO)

from pymilvus import MilvusClient

# URI   = "https://in03-b24fbf72fa83f44.serverless.gcp-us-west1.cloud.zilliz.com"
# TOKEN = "REDACTED_API_KEY"  # your Data API key from the cluster (not org/account key)
URI="https://in03-b24fbf72fa83f44.serverless.gcp-us-west1.cloud.zilliz.com"
TOKEN="cd56cdc1cd483caa402da6cc5846d5a2cbeb6e6ca1e9c99e718672027b4ef2fc51b43e507d1220a8ca89c2e199c922e0f86b539d"  # paste exactly as shown in console


client = MilvusClient(
    uri=URI,
    token=TOKEN,
    db_name="default",   # required on some serverless clusters
    timeout=30
)

print("✅ Connected")
print("Collections:", client.list_collections())
# PY

# from pymilvus import MilvusClient
# try:
#     MilvusClient(uri=URI, token=TOKEN, db_name="default", timeout=30)
#     print("ok")
# except Exception as e:
#     import traceback; traceback.print_exc()
