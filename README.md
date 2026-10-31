# Seven Digest

Pipeline Python para transformar commits de repositórios configurados em um resumo semanal: coleta, classificação e síntese com LLM, geração de PDF, arquivamento e entrega opcional via WhatsApp. O manifesto exige Python 3.12 ou superior.

## Configuração e efeitos da execução

A CLI lê `digest.config.yaml` e usa `OPENAI_API_KEY`; o envio WhatsApp usa `META_ACCESS_TOKEN` quando há destinatários configurados. Configure apenas repositórios e destinatários autorizados. A classificação envia conteúdo ao provedor de LLM e pode gerar custos. O arquivamento pode fazer commit e push quando habilitado na configuração.

`--dry-run` desativa o envio WhatsApp e o commit/push do fluxo, mas continua coletando dados, usando o LLM e gravando PDF e arquivos locais. Portanto, esse modo não é uma simulação offline nem uma garantia de ausência de custos.

A suíte inclui testes unitários e smoke tests de integração. O comando padrão do pytest exclui `tests/smoke`; esses testes de integração usam serviços externos.

## Execução local

```
python -m pip install -e ".[dev]"
python -m digest_engine --week 2026-W17
```

## Configuração

Edite `digest.config.yaml` para definir repositórios, modelo, identidade visual, arquivamento e destinatários.
