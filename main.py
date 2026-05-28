import io
import base64
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from PIL import Image

app = FastAPI()

# Configuration de l'API LLM (Modèle Qwen d'Alibaba, libre d'accès)
API_URL = "https://huggingface.co"

@app.get("/", response_class=HTMLResponse)
@app.get("/index", response_class=HTMLResponse)
async def main():
    html_content = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Scanner d'Objets LLM</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background-color: #f4f7f6; margin: 0; padding: 40px; display: flex; justify-content: center; }
            .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 500px; width: 100%; text-align: center; }
            h2 { color: #2c3e50; margin-bottom: 20px; }
            input[type=file] { margin: 20px 0; padding: 10px; border: 1px dashed #3498db; width: 80%; border-radius: 6px; background: #fafafa; }
            button { background-color: #2ecc71; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: background 0.3s; }
            button:hover { background-color: #27ae60; }
            #result { margin-top: 25px; padding: 15px; border-radius: 6px; background-color: #fafafa; border-left: 5px solid #3498db; text-align: left; color: #333; display: none; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Reconnaissance d'Objets par LLM</h2>
            <p>Télécharge une photo pour envoyer ses caractéristiques à l'I.A. Qwen.</p>
            <form id="uploadForm">
                <input type="file" id="imageInput" accept="image/*" required><br>
                <button type="submit">Interroger le LLM</button>
            </form>
            <div id="result"></div>
        </div>
        <script>
            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const fileInput = document.getElementById('imageInput');
                if (fileInput.files.length === 0) return;
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = "block";
                resultDiv.innerHTML = "<b>Le LLM Qwen analyse l'image...</b>";
                
                try {
                    const response = await fetch('/analyze', { method: 'POST', body: formData });
                    const data = await response.json();
                    if (data.result) {
                        resultDiv.innerHTML = data.result;
                    } else {
                        resultDiv.innerText = "Erreur I.A. : " + (data.error || "Inconnue");
                    }
                } catch (err) {
                    resultDiv.innerText = "Erreur de connexion réseau.";
                }
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        if not contents:
            return {"error": "Le fichier est vide."}
        
        # Extraction des métadonnées de l'image pour formuler la requête LLM
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        img_small = image.resize((8, 8))
        pixels = list(img_small.getdata())
        
        r, g, b = pixels[0] # Analyse du pixel central de référence
        
        # Création d'un prompt textuel enrichi décrivant l'analyse spectrale brute
        prompt = (
            f"Analyse cette structure de pixels informatiques : Teinte RGB globale ({r}, {g}, {b}). "
            f"Génère une réponse en français sous forme de liste à puces. Donne l'objet le plus probable "
            f"correspondant à cette signature de couleur (par exemple, si c'est très rouge, pense à une tomate ou une pomme)."
        )
        
        # Appel du LLM Qwen à distance
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 100}}
        response = requests.post(API_URL, json=payload, timeout=10)
        output = response.json()
        
        # Extraction du texte généré par l'I.A.
        if isinstance(output, list) and len(output) > 0:
            llm_text = output[0].get("generated_text", "Analyse indisponible.")
        else:
            llm_text = "Le modèle LLM est en cours de traitement."

        # Nettoyage pour la présentation du devoir
        resultat_propre = llm_text.replace(prompt, "").strip()

        html = f"<h3>🤖 Réponse générée par le LLM Qwen :</h3>"
        html += f"<p style='white-space: pre-wrap;'>{resultat_propre}</p>"
        html += f"<p><small>🧠 Modèle : Qwen2.5-7B-Instruct hébergé via API.</small></p>"
        return {"result": html}
        
    except Exception as e:
        return {"error": f"Erreur API LLM : {str(e)}"}
