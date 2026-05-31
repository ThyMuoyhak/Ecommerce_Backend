from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import re
import jwt
from config import settings

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Public paths - no authentication needed
        public_paths = [
            '/api/auth/login',
            '/api/auth/register',
            '/api/auth/logout',
            '/api/products',
            '/api/categories',
            '/health',
            '/',
            '/docs',
            '/openapi.json',
            '/redoc',
            '/api/payment/webhook',
            '/api/payment/verify',
        ]
        
        # Also allow static files (images, CSS, etc.)
        if path.startswith('/static/'):
            return await call_next(request)
        
        # Check if the current path starts with any public prefix
        is_public = False
        for prefix in public_paths:
            if path == prefix or path.startswith(prefix + '/'):
                is_public = True
                break
        
        # Allow OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip authentication for public paths
        if is_public:
            return await call_next(request)
        
        # For protected routes, check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return Response(
                content='{"detail": "Not authenticated"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type='application/json'
            )
        
        try:
            # Extract token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return Response(
                    content='{"detail": "Invalid authorization header"}',
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    media_type='application/json'
                )
            
            token = parts[1]
            
            # Decode token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Store user info in request state
            request.state.user_id = payload.get('sub')
            request.state.user_role = payload.get('role')
            
            # Check admin access for admin routes
            if path.startswith('/api/admin'):
                if request.state.user_role != 'admin':
                    return Response(
                        content='{"detail": "Admin access required"}',
                        status_code=status.HTTP_403_FORBIDDEN,
                        media_type='application/json'
                    )
            
            return await call_next(request)
            
        except jwt.ExpiredSignatureError:
            return Response(
                content='{"detail": "Token expired"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type='application/json'
            )
        except jwt.InvalidTokenError:
            return Response(
                content='{"detail": "Invalid token"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type='application/json'
            )
        except Exception as e:
            print(f"Auth middleware error: {e}")
            return Response(
                content='{"detail": "Authentication error"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type='application/json'
            )