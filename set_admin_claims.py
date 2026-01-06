"""Set admin custom claims for a Firebase user"""
import firebase_admin
from firebase_admin import credentials, auth
import os

# Initialize Firebase Admin
cred_path = os.getenv("FIREBASE_CREDENTIALS", "path/to/serviceAccountKey.json")
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

# Set your email here
USER_EMAIL = "udayvarma0206@gmail.com"

try:
    user = auth.get_user_by_email(USER_EMAIL)
    auth.set_custom_user_claims(user.uid, {'admin': True})
    print(f"✅ Admin claims set for {USER_EMAIL}")
    print(f"User UID: {user.uid}")
    print("Log out and log back in to apply changes.")
except Exception as e:
    print(f"❌ Error: {e}")
