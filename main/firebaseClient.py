import os
import sys
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


class FirebaseClient:
    def __init__(self):
        firebaseDatabaseURL = os.environ["FIREBASE_URL"]
        firebaseCredentialPath = os.path.join("secrets", "firebase", "firebase-credential.json")
        try:
            firebase_admin.initialize_app(credentials.Certificate(firebaseCredentialPath), {"databaseURL": firebaseDatabaseURL})
        except Exception as e:
            sys.exit(f"Firebase initialization failed. Error:\n{e}")

    def getTrip(self, tripId: str):
        """
        取得特定的 trip data\n
        找不到時回傳 None
        """
        return db.reference(f"/TRIP/{tripId}").get()
