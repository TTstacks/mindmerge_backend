from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.core.cache import cache
from backend.settings import SUPABASE_URL
import jwt
from jwt import PyJWKClient, PyJWK

class SupabaseJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        token = auth_header.split()[1]

        try:
            url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
            
            jwks_client=  PyJWKClient(url)
            

            signing_key = jwks_client.get_signing_key_from_jwt(token)
            

            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["ES256"],
                options={
                    "verify_aud": False,
                    "verify_signature": True
                }
            )
        except Exception as e:
            raise AuthenticationFailed(str(e))
        

        user_id = payload.get('sub')
        if not user_id:
            raise AuthenticationFailed('invalid token payload')
        
        try:
            user = get_user_model().objects.get(supabase_uid=user_id)
        except get_user_model().DoesNotExist:
            raise AuthenticationFailed('user does not exist')
        

        return (user, payload)
            
        
        
