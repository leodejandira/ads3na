from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from app.api.routers import auth_router

app = FastAPI()

templates = Jinja2Templates(directory="templates")


# @app.get("/", response_class=HTMLResponse)
# async def render_index(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})


app.include_router(auth_router.router, tags=["Autenticação"])


@app.get("/")
def read_root():
    return {"message": "API está no ar!"}
