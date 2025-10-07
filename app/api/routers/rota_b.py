from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def verify_role(request: Request, required_role: str):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

@router.get("/rota-b", response_class=HTMLResponse)
async def rota_b(request: Request):
    verify_role(request, "B")
    return templates.TemplateResponse("rota_b.html", {"request": request})
