from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib, os

app = FastAPI(title="Iris API")

model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
data = joblib.load(model_path)
model = data["model"]
target_names = data["target_names"]

class IrisInput(BaseModel):
    features: list[float]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predecir")
def predecir(input: IrisInput):
    if len(input.features) != 4:
        raise HTTPException(status_code=400, detail="Se necesitan exactamente 4 valores")
    prediction = model.predict([input.features])[0]
    probs      = model.predict_proba([input.features])[0]
    return {
        "clase":   int(prediction),
        "especie": target_names[prediction],
        "probabilidades": {n: round(float(p), 4) for n, p in zip(target_names, probs)}
    }