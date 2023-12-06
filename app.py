from flask import Flask,render_template, request, Response
import os
import openai
from time import sleep
import tiktoken

app = Flask(__name__)
secret_key  = 'SUA_CHAVE_DA_API'


openai.api_key = secret_key

def carrega(nome_do_arquivo):
    try:
        with open(nome_do_arquivo, "r") as arquivo:
            dados = arquivo.read()
            return dados
    except IOError as e:
        print(f"Erro no carregamento de arquivo: {e}")

def salva(nome_do_arquivo, conteudo):
    try:
        with open(nome_do_arquivo, "a", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
    except IOError as e:
        print(f"Erro ao salvar arquivo: {e}")


def bot(prompt,historico):
    maxima_repeticao = 1
    repeticao = 0
    while True:
        try:
            model='gpt-3.5-turbo'
            prompt_do_sistema = f"""
            Você está interagindo com um chatbot de atendimento psicológico. Lembre-se de que eu sou um assistente virtual e não substituo a orientação de um profissional de saúde mental licenciado. Por favor, sinta-se à vontade para compartilhar seus sentimentos e pensamentos, e farei o meu melhor para fornece.
            Você deve ser capaz de entender as emoções e sentimentos dos usuários, respondendo de maneira sensível e solidária!
            Você Além de ser útil, pode incluir interações lúdicas, como piadas leves, enigmas ou jogos simples para tornar as conversas mais envolventes.
            Seu nome é Bibi.
            Você Não substitui um profissional, você pode escutar o usuário e fornecer respostas de ajuda.
            Você não deve aceitar palavras de baixo calão ou de interpretação sexual.
            ## Historico:
            {historico}
            """
            tamanho_esperado_saida = 2000
            total_de_tokens_modelo = 4000
            if conta_tokens(prompt_do_sistema) >= total_de_tokens_modelo - tamanho_esperado_saida:
                model = 'gpt-3.5-turbo-16k'

            response = openai.ChatCompletion.create(
                messages=[
                    {
                        "role": "system",
                        "content": prompt_do_sistema
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream = True,
                temperature=1,
                max_tokens=255,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                model = model)
            return response
        except Exception as erro:
            repeticao += 1
            if repeticao >= maxima_repeticao:
                return "Erro no GPT3: %s" % erro
            print('Erro de comunicação com OpenAI:', erro)
            sleep(1)

#conta o tamanho do token

def conta_tokens(prompt):
    codificador = tiktoken.encoding_for_model("gpt-3.5-turbo")
    lista_de_tokens = codificador.encode(prompt)
    contagem = len(lista_de_tokens)
    return contagem


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods = ['POST'])
def chat():
    prompt = request.json['msg']
    nome_do_arquivo = 'historico_chat'
    historico = ''
    if os.path.exists(nome_do_arquivo):
        historico = carrega(nome_do_arquivo)
    return Response(trata_resposta(prompt,historico,nome_do_arquivo), mimetype = 'text/event-stream')

def trata_resposta(prompt,historico,nome_do_arquivo):
    resposta_parcial = ''
    for resposta in bot(prompt,historico):
        pedaco_da_resposta = resposta.choices[0].delta.get('content','')
        if len(pedaco_da_resposta):
            resposta_parcial += pedaco_da_resposta
            yield pedaco_da_resposta 
    conteudo = f"""
    Usuário: {prompt}
    IA: {resposta_parcial}    
    """
    salva(nome_do_arquivo,conteudo)
    
if __name__ == "__main__":
    app.run(debug = True)