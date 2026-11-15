# Teste de usabilidade do caso de referência

Evidência das issues #104 (validar o caso de referência) e #56 (US-012, concluir a comparação).

O roteiro de teste combinado pela equipe (passos 1 a 8) é executado no navegador como uma pessoa faria: digitando letra
por letra, passando o mouse antes de clicar, rolando a página e parando para ler. Cada "✔" do roteiro vira um item
conferido, cada passo tem captura de tela e cada sessão é gravada em vídeo.

- Resultado e parecer: [RELATORIO.md](RELATORIO.md)
- Vídeos das sessões: `videos/` (computador 1280 × 800 e celular 390 × 844)
- Capturas por passo: `capturas/`

## Como repetir

Na pasta `frontend`:

```
npm run test:usabilidade
```

Usa o Microsoft Edge instalado; sobe a API e o site se não estiverem rodando; leva alguns minutos, porque segue o
ritmo de uma pessoa. Cada execução regrava o relatório, as capturas e os vídeos.

## Diferença para a bateria técnica

A bateria em [../testes-e2e/](../testes-e2e/) cobre casos isolados e checagens da API, no ritmo da máquina. Este teste
percorre o roteiro inteiro numa sessão contínua, na ordem em que um produtor usaria o TELLUS.

## Limite

Não substitui um teste com produtores reais: o SC-001 da spec 012 fala em 5 de 5 participantes. O que este teste
garante é que o fluxo do roteiro funciona do começo ao fim, com o resultado real, no computador e no celular.
