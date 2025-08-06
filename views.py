from PIL import Image, ImageDraw, ImageFont
import pytesseract
from googletrans import Translator
from flask import request, jsonify
from main import app
import base64
import io 

MAPA_GOOGLETRA = {
    'eng': 'en',
    'por': 'pt',
    'jpn': 'ja',
    'chi_sim': 'zh-CN', 
    'kor': 'ko',
    'spa': 'es',
    # Incluir também os códigos ISO para caso venham do frontend (para idioma_novo)
    'en': 'en',
    'pt': 'pt',
    'ja': 'ja',
    'zh': 'zh-CN', 
    'ko': 'ko',
    'es': 'es',
}

# Iniciar código
@app.route("/", methods=["POST"])
def traduzir_imagem():
    dados = request.get_json()
    idioma_atual_raw = dados.get('atual')
    idioma_novo_raw = dados.get('novo')
    imagem_base64 = dados.get('imagem')

    # Verifica se a imagem foi enviada
    if not imagem_base64:
        return jsonify({"error": "Nenhuma imagem foi enviada.", "texto_traduzido": "Erro."}), 400


    # Alterações na imagem
    if "base64," in imagem_base64:
        imagem_base64 = imagem_base64.split("base64,")[1]
    try:
        imagem_bytes = base64.b64decode(imagem_base64)
        screenshot_pil = Image.open(io.BytesIO(imagem_bytes))
    except Exception as e:
        return jsonify({"error": f"Erro ao decodificar a imagem: {e}", "texto_traduzido": "Erro."}), 400
    
    idioma_atual_gt = MAPA_GOOGLETRA.get(idioma_atual_raw, idioma_atual_raw)
    idioma_novo_gt = MAPA_GOOGLETRA.get(idioma_novo_raw, idioma_novo_raw)

    traducao = capturar_traduzir(screenshot_pil, idioma_atual_raw, idioma_novo_gt, idioma_atual_gt)
    
    # Retorna o resultado como JSON
    return jsonify(traducao)



# Codigo para print e tradução
def capturar_traduzir(imagem_pil, idioma_atual_tesseract, idioma_novo_googletrans, idioma_atual_googletrans):
    try:
        # Executar OCR com bounding boxes
        info = pytesseract.image_to_data(imagem_pil, lang=idioma_atual_tesseract, output_type=pytesseract.Output.DICT)

        desenho = ImageDraw.Draw(imagem_pil)
        fonte = ImageFont.truetype("arial.ttf", 20)
        tradutor = Translator()

        parte_traduzido = []

# Loop pelas caixas de texto

        for i in range(len(info['text'])):
            texto = info['text'][i].strip()
            if texto:
                x, y, w, h = info['left'][i], info['top'][i], info['width'][i], info['height'][i]

# Traduzir texto
                try:
                    texto_traduzido = tradutor.translate(texto, src=idioma_atual_googletrans, dest=idioma_novo_googletrans).text
                    parte_traduzido.append(texto_traduzido)
                except Exception as e:
                    texto_traduzido = texto + " (erro trad.)"
                    parte_traduzido.append(texto_traduzido)

                # Apaga texto original
                desenho.rectangle([(x, y), (x + w, y + h)], fill="white")
                # Desenha texto traduzido
                desenho.text((x, y), texto_traduzido, fill="black", font=fonte)

        # Converter imagem final para base64
        buffer = io.BytesIO()
        imagem_pil.save(buffer, format="PNG")
        imagem_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "imagem_modificada": f"data:image/png;base64,{imagem_base64}",
            "texto_traduzido": "\n".join(parte_traduzido)
        }

    except Exception as e:
        return {"error": f"Erro ao processar imagem: {e}", "texto_traduzido": "Erro"}