# 0005 Worklog

- Commit title: `feat: implement backend auth domain and routes`
- Scope: `backend`

## Changed Files

- `backend/app/core/error.py`
- `backend/app/models/__init__.py`
- `backend/app/models/user.py`
- `backend/app/services/__init__.py`
- `backend/app/services/auth.py`
- `backend/app/routers/__init__.py`
- `backend/app/routers/v1/__init__.py`
- `backend/app/routers/v1/auth.py`
- `backend/app/utils/__init__.py`
- `backend/app/utils/security.py`
- `backend/app/utils/token.py`
- `backend/app/utils/cookies.py`
- `worklog/0005-backend-auth-domain-and-routes.md`

## Reason

- Add user/auth data models, DTO/DAO flow, and validation schemas.
- Implement signup/login/refresh/logout service logic with lockout handling.
- Expose auth API endpoints and service-level error mapping.

## Impact

- Backend now provides full auth lifecycle endpoints.
- Error payload format is consistent for frontend handling.
