import os

import dotenv
import firebase_admin
from firebase_admin import credentials

dotenv.load_dotenv()

GOOGLE_APPLICATION_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH")
if not GOOGLE_APPLICATION_CREDENTIALS_PATH:
    raise EnvironmentError(
        "The environment variable 'GOOGLE_APPLICATION_CREDENTIALS_PATH' is not set. "
        "Please set it in your .env file or environment."
    )

ABS_GOOGLE_APPLICATION_CREDENTIALS_PATH = os.path.expanduser(GOOGLE_APPLICATION_CREDENTIALS_PATH)
cred = credentials.Certificate(ABS_GOOGLE_APPLICATION_CREDENTIALS_PATH)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
