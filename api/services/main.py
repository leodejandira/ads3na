from fastapi import FastAPI

app = FastAPI()

@app.get("/double/{value}")
async def double_value(value: int):
    return {"result": value * 2}


@app.get("/")
async def root():
    return {"message": "API está rodando! Use /double/{value}"}