document.addEventListener('DOMContentLoaded', function() {
    const imagensContainer = document.getElementById('imagens-container');

    // Recupera os dados do armazenamento local
    chrome.storage.local.get('imagensTraduzidas', function(data) {
        if (chrome.runtime.lastError || !data.imagensTraduzidas) {
            imagensContainer.textContent = "Erro ao carregar as imagens.";
            console.error("Erro ao carregar imagens:", chrome.runtime.lastError);
            return;
        }

        const imagens = data.imagensTraduzidas;
        if (imagens.length === 0) {
            imagensContainer.textContent = "Nenhuma imagem traduzida encontrada.";
            return;
        }

        // Itera sobre as imagens e as exibe
        imagens.forEach(imagemBase64 => {
            const imgElement = document.createElement('img');
            imgElement.src = imagemBase64;
            imgElement.classList.add('imagem-traduzida');
            imagensContainer.appendChild(imgElement);
        });

        // Limpa o armazenamento local para liberar espaço
        chrome.storage.local.remove('imagensTraduzidas');
    });
});