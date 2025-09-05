from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as nb
import pytesseract
from googletrans import Translator
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import base64
import io

app = Flask(__name__)
CORS(app)

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

# Rota principal para o pop-up
@app.route("/")
def popup():
    return render_template("popup.html")

# Rota para a tradução
@app.route("/", methods=["POST"])
def traduzir_imagem():
    dados = request.get_json()
    idioma_atual_raw = dados.get('atual')
    idioma_novo_raw = dados.get('novo')
    listaPrints = dados.get('imagem')

    if not listaPrints:
        return jsonify({"error": "Nenhuma imagem foi enviada.", "texto_traduzido": "Erro."}), 400

    imagens_processadas = []

    for imagem_base64 in listaPrints:
        try:
            if "base64," in imagem_base64:
                imagem_base64 = imagem_base64.split("base64,")[1]
            imagem_bytes = base64.b64decode(imagem_base64)
            screenshot_pil = Image.open(io.BytesIO(imagem_bytes))
            imagem_original = screenshot_pil.copy()
            img = cv2.cvtColor(nb.array(screenshot_pil), cv2.COLOR_RGB2BGR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.Laplacian(img, cv2.CV_8U)
            _, imagem_processada = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY_INV)

            imagens_processadas.append({
                'processada': imagem_processada,
                'original': imagem_original
            })
        except Exception as e:
            return jsonify({"error": f"Erro ao decodificar a imagem: {e}", "texto_traduzido": "Erro."}), 400

    idioma_atual_gt = MAPA_GOOGLETRA.get(idioma_atual_raw, idioma_atual_raw)
    idioma_novo_gt = MAPA_GOOGLETRA.get(idioma_novo_raw, idioma_novo_raw)

    traducao = capturar_traduzir(
        imagens_processadas, idioma_atual_raw, idioma_novo_gt, idioma_atual_gt)

    return jsonify(traducao)

# Codigo para print e tradução
def capturar_traduzir(imagens_processadas, idioma_atual_tesseract, idioma_novo_googletrans, idioma_atual_googletrans):
    textos_traduzido = []  # Guarda todos os textos de todas as imagens
    imagens_traduzidas = []  # Guarda as imagens traduzidas em Base64
    tradutor = Translator()

    for imagem in imagens_processadas:
        try:
            imagem_processada = imagem['processada']
            imagem_original = imagem['original']
            info = pytesseract.image_to_data(
                imagem_processada, lang=idioma_atual_tesseract, output_type=pytesseract.Output.DICT)

            desenho = ImageDraw.Draw(imagem_original)
            fonte = ImageFont.truetype("arial.ttf", 20)

            texto_da_imagem = [] # Guarda o texto da imagem que está passando agora

            blocos = [i for i, lvl in enumerate(info['level']) if lvl == 2]
            
            for i in blocos:
                num_bloco = info['block_num'][i]
                texto_bloco = []
                for j in range(len(info['level'])):
                    if info['level'][j] == 5 and info['block_num'][j] == num_bloco:
                        if int(info['conf'][j]) != -1:
                            palavra = info['text'][j].strip()
                            if palavra:
                                texto_bloco.append(palavra)

                texto = " ".join(texto_bloco)
                if texto:
                    x, y, w, h = info['left'][i], info['top'][i], info['width'][i], info['height'][i]
                    try:
                        texto_traduzido = tradutor.translate(
                            texto, src=idioma_atual_googletrans, dest=idioma_novo_googletrans).text
                        texto_da_imagem.append(texto_traduzido)
                    except Exception as e:
                        texto_traduzido = texto + " (erro trad.)"
                        texto_da_imagem.append(texto_traduzido)

                    largura = w
                    linha = []
                    separado = texto_traduzido.split()
                    linha_atual = ""

                    for s in separado:
                        teste = linha_atual + (" " if linha_atual else "") + s
                        caixa = fonte.getbbox(teste)
                        linha_largura = caixa[2] - caixa[0]
                        if linha_largura <= largura:
                            linha_atual = teste
                        else:
                            linha.append(linha_atual)
                            linha_atual = s

                    if linha_atual:
                        linha.append(linha_atual)

                    desenho.rectangle([(x, y), (x + w, y + h)], fill="white")

                    caixa = fonte.getbbox('A')
                    linha_altura = caixa[3] - caixa[1]
                    for l, line in enumerate(linha):
                        desenho.text((x, y + l * linha_altura), line, fill="black", font=fonte)

            textos_traduzido.extend(texto_da_imagem)

            buffer = io.BytesIO()
            imagem_original.save(buffer, format="PNG")
            imagem_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            imagens_traduzidas.append(f"data:image/png;base64,{imagem_base64}")

        except Exception as e:
            textos_traduzido.append("Erro ao traduzir: " + str(e))
            imagens_traduzidas.append(None)
            continue

    return {
        "imagens_modificada": imagens_traduzidas,
        "texto_traduzido": "\n".join(textos_traduzido)
    }

if __name__ == "__main__":
    app.run(debug=False)