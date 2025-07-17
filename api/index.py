from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mangum import Mangum
app = FastAPI()

@app.get("/")
def read_root():
    return JSONResponse(content={"message": "Hello from FastAPI on Vercel!"})

handler = Mangum(app)
