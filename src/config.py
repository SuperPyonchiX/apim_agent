import os

from dotenv import load_dotenv

load_dotenv()

AZURE_APIM_ENDPOINT: str = os.environ["AZURE_APIM_ENDPOINT"]
AZURE_APIM_SUBSCRIPTION_KEY: str = os.environ["AZURE_APIM_SUBSCRIPTION_KEY"]
AZURE_API_VERSION: str = os.environ.get("AZURE_API_VERSION", "2025-04-01-preview")
AZURE_DEPLOYMENT_NAME: str = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o")
CLIENT_APPROACH: str = os.environ.get("CLIENT_APPROACH", "azure")
