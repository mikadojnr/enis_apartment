import idanalyzer
import os
from flask import current_app
from werkzeug.utils import secure_filename
from app.models import VerifiedID, db
from datetime import datetime

class IDVerifier:
    def __init__(self):
        self.api_key = current_app.config.get('IDANALYZER_API_KEY')
        self.region = current_app.config.get('IDANALYZER_REGION', 'US')
        if not self.api_key:
            raise ValueError("IDANALYZER_API_KEY is not configured")

    def verify_document(self, document_file, id_type="nin", email=None, user_id=None):
        """
        Verify ID document with optional face match.
        document_file: FileStorage object from request.files
        """
        try:
            # Initialize Core API
            coreapi = idanalyzer.CoreAPI(self.api_key, self.region)
            coreapi.throw_api_exception(True)        # Raise exceptions on API errors

            # Enable quick authentication (fake ID detection)
            coreapi.enable_authentication(True, 'quick')

            # Save uploaded file temporarily
            filename = secure_filename(document_file.filename)
            temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, filename)
            document_file.save(temp_path)

            # For production: serve this file publicly or use base64.
            # Here we assume your /uploads is served statically.
            document_url = f"/uploads/temp/{filename}"

            # Perform scan (document only for now - add biometric_photo later)
            response = coreapi.scan(document_primary=document_url)

            # Clean up temp file
            # os.remove(temp_path)   # Uncomment after testing

            if response.get('result'):
                data = response['result']

                # Store successful verification
                verified = VerifiedID(
                    user_id=user_id,
                    email=email,
                    id_type=id_type,
                    id_number=data.get('documentNumber') or data.get('idNumber'),
                    full_name=f"{data.get('firstName','')} {data.get('lastName','')}".strip(),
                    date_of_birth=data.get('dob'),
                    verification_id=response.get('transactionId'),
                    document_url=document_url,
                    is_verified=True
                )
                db.session.add(verified)
                db.session.commit()

                return {
                    "success": True,
                    "verified_id_id": verified.id,
                    "full_name": verified.full_name,
                    "data": data,
                    "authentication": response.get('authentication'),
                    "face": response.get('face')
                }

            return {"success": False, "message": "No result from ID Analyzer"}

        except idanalyzer.APIError as e:
            details = e.args[0]
            return {
                "success": False,
                "message": f"API Error {details.get('code')}: {details.get('message')}"
            }
        except Exception as e:
            current_app.logger.error(f"ID Verification error: {str(e)}", exc_info=True)
            return {"success": False, "message": "Internal verification error"}

# Create a global instance
id_verifier = IDVerifier()