from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "你好"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=83)
