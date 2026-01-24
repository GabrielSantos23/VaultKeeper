# Como funciona essa bagaça? (Guia Informal do VaultKeeper)

E aí! Se você tá lendo isso, provavelmente quer entender como o **VaultKeeper** funciona por baixo dos panos sem ter que decifrar milhares de linhas de código sozinho. Vou te explicar tudo de um jeito bem direto, como se a gente estivesse tomando um café (ou uma cerveja) e trocando ideia sobre o projeto.

O VaultKeeper não é só uma extensão de navegador; ele é um sistema **híbrido**. Ele tem um "cérebro" poderoso rodando no seu computador (Python) e "olhos/mãos" ágeis no seu navegador (Extensão).

---

## 🏗️ A Arquitetura: O Trio Parada Dura

O sistema é dividido em três partes principais que conversam entre si o tempo todo:

1.  **O Cofre (Python/Desktop App):** Onde os dados realmente vivem.
2.  **A Ponte (Native Messaging Host):** O tradutor que permite o navegador falar com o Python.
3.  **A Extensão (Browser):** A interface que você vê e que interage com os sites.

> **[ESPAÇO PARA IMAGEM: Diagrama mostrando o App Python, o Native Host no meio e a Extensão no navegador, conectados por setas]**

---

## 🚦 O Native Host: O Que é Isso?

Antes de falar das funcionalidades, precisamos falar desse cara. Navegadores modernos (Chrome, Firefox) funcionam numa "caixa de areia" (sandbox). Eles não podem ler seus arquivos nem rodar comandos no seu PC por segurança.

Para o VaultKeeper ser poderoso, ele precisa sair dessa caixa. É aí que entra o **Native Native Host**.

- **O Que é?** É um protocolo oficial dos navegadores que permite conversar com um programa instalado no seu computador.
- **Como Funciona?** O navegador inicia o nosso script (`app/native/host.py`) e conversa com ele usando a entrada e saída padrão (`stdin` e `stdout`).

Olha como o Python lê as mensagens que vêm do Chrome:

```python
# app/native/host.py

def read_message(self) -> Optional[Dict[str, Any]]:
    # 1. Lê exatos 4 bytes para saber o tamanho da mensagem (é binário, baby!)
    length_bytes = sys.stdin.buffer.read(4)

    if len(length_bytes) != 4: return None

    # 2. Converte esses bytes pra saber quantos bytes ler a seguir
    message_length = struct.unpack('@I', length_bytes)[0]

    # 3. Lê o JSON real
    message_bytes = sys.stdin.buffer.read(message_length)
    return json.loads(message_bytes.decode('utf-8'))
```

Isso significa que a extensão manda um JSON `{"action": "get_credentials"}`, o Host lê, consulta o banco, e responde `{"success": true, ...}`.

---

## 🛠️ O Que Mais Essa Máquina Faz?

O VaultKeeper é cheio de features extras escondidas no código Python.

### 1. Sincronização com Google Drive (Opcional)

Se o seu PC queimar, você perde tudo? Não se ativar o Google Drive.

- **Como Funciona:** Nós usamos a API oficial do Google Drive. Mas tem um truque: o `app/core/gdrive.py` sobe um mini servidor HTTP local na porta 58392 só pra receber o código de autorização do Google (`OAuthCallbackHandler`).
- **O Que é Salvo?** A gente pega o seu arquivo `vault.db` (que já é criptografado, lembra?) e joga ele inteiro numa pasta segura no seu Drive.

```python
# app/core/gdrive.py

def upload_vault(self, vault_path: Path = None):
    # Procura (ou cria) a pasta 'VaultKeeper' no seu Drive
    folder_id = self._get_or_create_vault_folder()

    # Sobe o arquivo database criptografado
    # ... código de upload ...
```

### 2. A Torre de Vigia (Watchtower)

Essa é a funcionalidade que te avisa se sua senha vazou. E o mais legal: **nós nunca enviamos sua senha para a internet**.

- **K-Anonymity:** Usamos uma técnica chamada K-Anonymity com a API do _Have I Been Pwned_.
  1.  Pegamos sua senha e geramos um hash SHA-1.
  2.  Pegamos só os **5 primeiros caracteres** desse hash.
  3.  Enviamos esses 5 caracteres para a API.
  4.  A API devolve _todos_ os vazamentos que começam com esses 5 caracteres.
  5.  O VaultKeeper verifica localmente se o resto do hash bate com o seu.

```python
# app/core/watchtower_service.py

def check_pwned(self, password: str) -> int:
    sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1_password[:5], sha1_password[5:]

    # Manda só o prefixo pra API!
    response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}")

    # Verifica o resto localmente
    for line in response.text.splitlines():
        hash_suffix, count = line.split(':')
        if hash_suffix == suffix:
            return int(count) # VAZOU!
    return 0
```

### 3. Gerador de Senhas

No `popup.js`, temos um algoritmo que gera caos controlado. Você escolhe o tamanho, se quer símbolos, números, etc., e nós geramos uma string criptograficamente segura usando o `crypto.getRandomValues()` do navegador.

### 4. Notas Seguras e Cartões de Crédito

Não guardamos apenas senhas. O banco de dados (`vault.db`) tem tabelas dedicadas para:

- **Secure Notes:** Textos livres criptografados (para guardar chaves de recuperação, diários secretos, etc).
- **Credit Cards:** Números de cartão, CVV e validade. Tudo criptografado com a mesma chave mestra.

```python
# app/core/vault.py

cursor.execute('''
    CREATE TABLE IF NOT EXISTS credit_cards (
        id INTEGER PRIMARY KEY,
        card_number BLOB NOT NULL, -- Blob criptografado
        cvv BLOB NOT NULL,         -- Blob criptografado
        ...
    )
''')
```

---

## 🧩 A Extensão e seus Desafios

### O Detetive de Campos (`content.js`)

Para preencher senhas automaticamente, a extensão injeta um script em **todas** as páginas. Ele tenta adivinhar o que é um campo de usuário e o que é senha baseando-se no HTML (`type="password"`, `name="username"`, etc).

> **[ESPAÇO PARA IMAGEM: Diagrama mostrando como o content.js identifica visualmente os campos na página]**

### O Problema do "Login em Dois Passos"

Sites como Google e Apple pedem o email numa tela, e a senha em outra. Isso quebrava o nosso "detetive".
**A Solução:** Quando você preenche o email, nós salvamos ele temporariamente na memória da aba (`sessionStorage`). Quando a tela de senha aparece, nós recuperamos esse email e juntamos as duas peças do quebra-cabeça.

```javascript
// extension/content.js

// Se achou senha mas não tem usuário na tela...
if (passwordField && !username) {
    // ...tenta resgatar o usuário que salvamos na tela anterior!
    const storedUsername = getMultiStepUsername();
    if (storedUsername) {
         return { username: storedUsername, password: ... };
    }
}
```

---

## 🏁 Conclusão

O VaultKeeper é um sistema complexo que tenta parecer simples. Ele usa:

1.  **Criptografia Pesada** (AES-256-GCM + Argon2) no Python.
2.  **Protocolos de Segurança** (K-Anonymity) para checar vazamentos.
3.  **Engenharia Reversa de DOM** (JavaScript) para preencher campos em sites modernos.

Tudo isso para garantir que sua única preocupação seja lembrar de **uma** senha mestra. O resto, a gente cuida. �
