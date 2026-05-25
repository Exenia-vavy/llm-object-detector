import io
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import torch

app = FastAPI()

# 1. Chargement du modèle MobileNetV2 officiel
model = models.mobilenet_v2(pretrained=True)
model.eval()

# 2. Base de données de traduction intégrée (Dictionnaire ImageNet principal)
TRADUCTIONS = {
    581: "Serre / Plantation (Greenhouse)",
    948: "Pomme (Apple)",
    950: "Orange / Agrume",
    917: "Grenade (Fruit)",
    923: "Assiette / Plat",
    954: "Banane (Banana)",
    665: "Téléphone portable / Smartphone",
    504: "Tasse / Mug",
    758: "Bouteille d'eau",
    931: "Citron",
    937: "Brocoli",
    920: "Poivron / Piment",
    499: "Clé / Clef",
    744: "Ordinateur portable",
    559: "Chaise / Fauteuil",
    849: "Table",
    601: "Planche à découper",
    477: "Couteau de cuisine"
}

# 3. Préparation mathématique de l'image
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

@app.get("/", response_class=HTMLResponse)
async def main():
    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Scanner d'Objets I.A.</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 40px; display: flex; justify-content: center; }
            .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 500px; width: 100%; text-align: center; }
            h2 { color: #2c3e50; margin-bottom: 20px; }
            input[type=file] { margin: 20px 0; padding: 10px; border: 1px dashed #3498db; width: 80%; border-radius: 6px; background: #fafafa; }
            button { background-color: #2ecc71; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: background 0.3s; }
            button:hover { background-color: #27ae60; }
            #result { margin-top: 25px; padding: 15px; border-radius: 6px; background-color: #fafafa; border-left: 5px solid #2ecc71; text-align: left; color: #333; display: none; line-height: 1.6; }
            .badge { background: #2ecc71; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>I.A. de Détection Neuronale Locale</h2>
            <p>Télécharge une photo pour que le réseau de neurones identifie l'objet exact.</p>
            <form id="uploadForm">
                <input type="file" id="imageInput" accept="image/*" required><br>
                <button type="submit">Analyser l'image</button>
            </form>
            <div id="result"></div>
        </div>

        <script>
            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const fileInput = document.getElementById('imageInput');
                const formData = new FormData();
                formData.append('file', fileInput.files[0]); // Correction ici : envoi du fichier précis

                const resultDiv = document.getElementById('result');
                resultDiv.style.display = "block";
                resultDiv.innerHTML = "<b>Analyse par le réseau de neurones en cours...</b>";

                try {
                    const response = await fetch('/analyze', { method: 'POST', body: formData });
                    const data = await response.json();
                    if (data.result) {
                        resultDiv.innerHTML = data.result;
                    } else {
                        // Affiche le vrai message d'erreur envoyé par Python
                        resultDiv.innerText = "Erreur du serveur : " + (data.error || "Inconnue");
                    }
                } catch (err) {
                    resultDiv.innerText = "Erreur de connexion réseau avec le serveur.";
                }
            };
        </script>
    </body>
    </html>
    """

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    try:
        # 1. Lecture brute des données du fichier
        contents = await file.read()
        if not contents:
            return {"error": "Le fichier envoyé est vide."}

        # 2. Ouverture de l'image et conversion immédiate pour nettoyer le format
        try:
            image = Image.open(io.BytesIO(contents))
            image = image.convert("RGB")
        except Exception as e_img:
            return {"error": f"Format d'image non lisible par Pillow : {str(e_img)}"}
        
        # 3. Redimensionnement de sécurité
        if image.width > 1200 or image.height > 1200:
            image.thumbnail((800, 800))
        
        # 4. Passage dans le réseau de neurones MobileNet
        input_tensor = transform(image).unsqueeze(0)
        
        with torch.no_grad():
            output = model(input_tensor)
        
        percentage = torch.nn.functional.softmax(output, dim=1) * 100
        _, indices = torch.sort(output, descending=True)
        
        # Extraction sécurisée du premier index scalaire
        top_idx = int(indices.flatten()[0].item())
        
        # Correspondance avec le dictionnaire
        nom_objet = TRADUCTIONS.get(top_idx, f"Objet (ImageNet ID #{top_idx})")
        confidence = round(percentage.flatten()[top_idx].item(), 1)

        html = f"<h3>🧠 Résultat de la Détection</h3>"
        html += f"<p><b>Élément identifié :</b> <span class='badge'>{nom_objet}</span></p>"
        html += f"<p><b>Indice de confiance :</b> {confidence}%</p>"
        html += f"<p><small>Analyse locale réussie via MobileNetV2.</small></p>"
        
        return {"result": html}
        
    except Exception as e:
        return {"error": f"Erreur interne du processeur I.A. : {str(e)}"}
