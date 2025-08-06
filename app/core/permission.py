from functools import wraps
from ..services.keycloak_service import KeycloakService
from fastapi import HTTPException, status


class permission:
    @staticmethod
    def hasPermission(role : str) :
        def authenticate(func: function) :
            @wraps(func)
            def wrapper(*args, **kwargs) : 
                keycloak_service = KeycloakService()
                if keycloak_service.has_role(role) :
                    func(args, kwargs)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not enough permissions"
                    )
            return wrapper
        return authenticate