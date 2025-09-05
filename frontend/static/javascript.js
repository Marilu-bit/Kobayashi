const listaPrints = [];

document.addEventListener('DOMContentLoaded', function() {
    
    //Para acionar a captura
    const capturar = document.getElementById('botaoCapturar');
    if (capturar) {
        capturar.addEventListener('click', BotaoCaptura);
    }

    //Para acinar a tradução
    const traduzir = document.getElementById('botaoTraduzir');
    if (traduzir) {
        traduzir.addEventListener('click', BotaoTraduzir);
    }
});

function BotaoCaptura(){
    chrome.tabs.captureVisibleTab(null, { format: 'png' }, function(dataUrl) {
        if (!chrome.runtime.lastError) {
            listaPrints.push(dataUrl);
            console.log("Captura adicionada à lista:", listaPrints);
        } else if(chrome.runtime.lastError) {
            console.error("Erro ao capturar a tela:", chrome.runtime.lastError.message);
            document.getElementById("status").textContent = "Erro: Não foi possível capturar a tela.";
            document.getElementById("TextoTraduzido").textContent = "Verifique as permissões da extensão.";
            return;
        }
    })
}



function BotaoTraduzir(){
    let idioma_atual = document.getElementById("idioma_atual").value;
    let idioma_novo = document.getElementById("idioma_novo").value;

    document.getElementById("status").textContent = "Traduzindo... Por favor, aguarde.";
    document.getElementById("TextoTraduzido").textContent = "Aguardando tradução...";
    document.getElementById("PrintTraduzido").innerHTML = "";

    // Envia as informações

        fetch("http://127.0.0.1:5000", { 
            method: "POST",
            headers:{
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                atual: idioma_atual,
                novo: idioma_novo,
                imagem: listaPrints 
            })
        })
        .then(response => {
            if (!response.ok) { // Verifica se a resposta foi bem-sucedida
                throw new Error('Erro na rede ou no servidor: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            // Esconder o status no pop-up pequeno
            document.getElementById("status").textContent = "Abrindo janela de tradução...";
        
            if (data.error) {
                document.getElementById("TextoTraduzido").textContent = "Erro: " + data.error;
                document.getElementById("status").textContent = "Erro na tradução.";
            } else if (data.imagens_modificada) {
                // Armazena a lista de imagens traduzidas no armazenamento local do Chrome
                chrome.storage.local.set({ 'imagensTraduzidas': data.imagens_modificada }, function() {
                    if (chrome.runtime.lastError) {
                        console.error("Erro ao salvar dados:", chrome.runtime.lastError);
                        return;
                    }
                    
                    // Calcula a posição central da tela
                    const width = 1700; // Largura da nova janela
                    const height = 1700; // Altura da nova janela
                    const left = (screen.width / 2) - (width / 2);
                    const top = (screen.height / 2) - (height / 2);
        
                    // Cria uma nova janela para exibir as imagens
                    chrome.windows.create({
                        url: chrome.runtime.getURL('templates/traduzido.html'),
                        type: 'popup',
                        width: width,
                        height: height,
                        left: left,
                        top: top
                    });
        
                    // Fecha o pop-up atual automaticamente (opcional)
                    window.close();
                });
        
            } else if (data.texto_traduzido) {
                document.getElementById("TextoTraduzido").textContent = data.texto_traduzido;
                document.getElementById("status").textContent = "Tradução concluída!";
            } else {
                document.getElementById("TextoTraduzido").textContent = "Resposta inesperada do servidor.";
                document.getElementById("status").textContent = "Erro.";
            }
        })}


