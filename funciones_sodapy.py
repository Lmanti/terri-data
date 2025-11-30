from dotenv import load_dotenv
import os
import pandas as pd
from sodapy import Socrata

load_dotenv()

APP_TOKEN = os.getenv("APP_TOKEN")

def cargar_json_sodapy(servername):
    client = Socrata("www.datos.gov.co", APP_TOKEN)
    results = client.get(servername)
    print("Datos cargados exitosamente.")
    return pd.DataFrame(results)