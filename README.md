# NonMouse

Aplicação que permite usar a mão como mouse, utilizando a webcam para reconhecer gestos e controlar o cursor.

## Requisitos

- Python 3.9 ou superior
- Webcam

## Instalação

```sh
git clone https://github.com/takeyamayuki/NonMouse
cd NonMouse
pip install -r requirements.txt
```

## Como executar

**Windows / Linux:**
```sh
python app.py
```

**macOS** (requer permissão de acessibilidade e câmera em Preferências do Sistema):
```sh
sudo python3 app.py
```

## Configurações iniciais

Ao iniciar o programa, uma tela de configuração será exibida:

- **Camera**: selecione o dispositivo de câmera (comece pelo número menor caso haja mais de uma).
- **How to place**: escolha como a câmera está posicionada:
  - `Normal` – câmera apontada para você (posição padrão de webcam).
  - `Above` – câmera posicionada acima da mão, apontada para baixo.
  - `Behind` – câmera atrás de você, apontada para o monitor.
- **Sensitivity**: ajuste a sensibilidade do cursor (valores muito altos causam tremor).

Clique em **Continue** para iniciar.

## Gestos da mão

> Segure `Alt` (Windows) ou `Command` (macOS) para ativar o controle por gestos. Funciona mesmo com a janela em segundo plano.

| Ação | Gesto |
|---|---|
| **Mover cursor** | Ponta do dedo indicador |
| **Parar cursor** | Encostar indicador no dedo médio |
| **Clique esquerdo** | Encostar polegar na segunda junta do indicador |
| **Soltar clique** | Separar polegar do indicador |
| **Duplo clique** | Dois cliques em menos de 0,5 segundos |
| **Clique direito** | Manter clique parado por 1,5 segundo |
| **Scroll** | Dobrar o indicador e mover |

**Dicas:**
- Use boa iluminação na mão.
- Mantenha a mão o mais plana possível em relação à câmera.

## Encerrar

- **Terminal ativo:** `Ctrl+C`
- **Janela do app ativa:** botão fechar (Windows/Linux) ou tecla `Esc`

## Build (opcional)

Os binários prontos estão disponíveis na [página de releases](https://github.com/takeyamayuki/NonMouse/releases).

Para gerar o executável manualmente:

**Windows:**
```sh
pip show mediapipe  # copie o caminho em "Location" para o campo datas no app-win.spec
pyinstaller app-win.spec
```

**macOS:**
```sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
pyinstaller app-mac.spec
```

## Licença

Veja o arquivo [LICENSE](LICENSE).
