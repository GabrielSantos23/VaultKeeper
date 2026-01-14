# Guia de Lançamento de Atualizações (Release Guide)

Este guia explica como lançar uma nova versão do VaultKeeper para que o sistema de atualização automática a detecte.

## Passo 1: Atualizar a Versão no Código

Antes de criar a release, você deve atualizar o número da versão no código da aplicação.

1. Abra o arquivo `app/__init__.py`.
2. Altere a variável `__version__` para a nova versão.

```python
# app/__init__.py
__version__ = "1.0.1"  # Exemplo: mudando de 1.0.0 para 1.0.1
```

## Passo 2: Commit e Push

Envie as alterações para o GitHub.

```bash
git add app/__init__.py
git commit -m "Bump version to 1.0.1"
git push origin main
```

## Passo 3: Criar uma Release no GitHub

O atualizador verifica as **Releases** do GitHub. Você precisa criar uma release oficial.

1. Acesse o repositório no GitHub: [https://github.com/GabrielSantos23/VaultKeeper](https://github.com/GabrielSantos23/VaultKeeper)
2. Clique em **Releases** (na barra lateral direita) ou vá em `Draft a new release`.
3. **Choose a tag**: Crie uma nova tag que corresponda à versão (ex: `v1.0.1`).
   - Importante: A tag deve começar com `v` seguido do número que você colocou no código.
4. **Release title**: Coloque um título (ex: "Versão 1.0.1 - Correções de Bugs").
5. **Description**: Descreva as mudanças.
6. **Assets** (Opcional, mas recomendado):
   - O GitHub cria automaticamente o "Source code (zip)" e "Source code (tar.gz)".
   - O sistema de atualização consegue baixar e instalar o "Source code" automaticamente.
   - Se você gerar um executável (.exe ou binário), anexe-o aqui se quiser que no futuro o sistema baixe o binário (o código atual prioriza zip/tar.gz, mas pode ser ajustado).
7. Clique em **Publish release**.

## Como funciona a atualização?

1. O usuário clica em "Check for Updates" no app.
2. O app consulta a API do GitHub para ver a última release.
3. Se a tag da última release (ex: `v1.0.1`) for maior que a versão local (`1.0.0`), ele avisa o usuário.
4. O usuário escolhe atualizar.
5. O app baixa o código fonte da nova versão, extrai e substitui os arquivos locais.
6. Ao reiniciar, o app estará rodando a nova versão.
