# MVP – Parte 1 (AV 03) – Projeto Aplicado I – Schulz S.A.

**Linguagem:** Python 3 (`sqlite3` da biblioteca padrão) | **Arquivos:** `04_classes.py`, `05_main.py`

## 1. O que foi feito

Nessa entrega a gente saiu da modelagem das AV 01 e 02 e partiu pro código de verdade. Implementamos em Python as classes de domínio (`Tecnico`, `Equipamento`, `Medicao`), uma classe de persistência (`BancoDados`) que fala com o SQLite, e um `05_main.py` que mostra tudo funcionando: cria o banco, insere dados de teste, faz UPDATE, roda um JOIN e imprime o relatório de calibração no terminal.

## 2. Padrões de POO usados

- **Encapsulamento:** atributos "protegidos" (`_matricula`, `_nome`, `_codigo_tag`) acessados via `@property` com setter. Se alguém tentar criar um técnico sem nome ou um equipamento sem TAG, estoura `ValueError`. A TAG também é normalizada pra maiúsculo.
- **Regra de negócio dentro do domínio:** a `Medicao` calcula o próprio `status`. O erro é `|valor_obtido − valor_referencia|` e, se for menor ou igual à tolerância, é `APROVADO`; senão, `REPROVADO`. Como `status` é uma property calculada, ninguém consegue gravar um status que não bate com os valores.
- **Separação de responsabilidades:** as classes de domínio não sabem nada de SQL; só a `BancoDados` conhece o banco. Se um dia trocar o SQLite por outro, mexe só nela.
- **Ponto único de execução SQL:** todo comando passa por `_executar()`, que faz `commit` se der certo e `rollback` se der erro.
- **Exceção própria:** `ErroBanco` embrulha os erros do `sqlite3`, então o resto do sistema só precisa tratar um tipo de erro.

## 3. Diagrama de classes (textual)

```
+------------------+     +----------------------+     +---------------------------+
| Tecnico          |     | Equipamento          |     | Medicao                   |
+------------------+     +----------------------+     +---------------------------+
| id_tecnico       |     | id_equipamento       |     | id_medicao                |
| matricula (prop) |     | codigo_tag (prop)    |     | id_equipamento (FK)       |
| nome (prop)      |     | descricao            |     | id_tecnico (FK)           |
| setor            |     | fabricante           |     | valor_referencia          |
+------------------+     +----------------------+     | valor_obtido, tolerancia  |
                                                      | data_medicao              |
                                                      +---------------------------+
                                                      | erro  (calculado)         |
                                                      | status (calculado)        |
                                                      +---------------------------+

+-------------------------------------------------------------------------+
| BancoDados                                                              |
+-------------------------------------------------------------------------+
| conn                                                                    |
+-------------------------------------------------------------------------+
| criar_tabelas()  fechar()  _executar(sql, params)                       |
| inserir_tecnico/equipamento/medicao()                                   |
| listar_tecnicos/equipamentos()  buscar_equipamento_por_tag()            |
| relatorio_calibracao()  (SELECT com JOIN)                               |
| atualizar_equipamento()  atualizar_medicao()                            |
+-------------------------------------------------------------------------+

Relações:  Tecnico 1 ----- N Medicao N ----- 1 Equipamento
           BancoDados usa (depende de) as 3 classes de domínio
```

## 4. Banco de dados (SQLite)

Três tabelas, as mesmas da AV 02: `tecnicos`, `equipamentos` e `medicoes`. `matricula` e `codigo_tag` são `UNIQUE`, `medicoes` tem chaves estrangeiras pras outras duas (com `PRAGMA foreign_keys = ON`) e um `CHECK` garantindo que o status só seja `APROVADO` ou `REPROVADO`.

> Obs.: os nomes das colunas de `medicoes` (valor_referencia, valor_obtido, tolerancia, etc.) seguem o que o grupo definiu na modelagem; qualquer ajuste fino é só alterar o `CREATE TABLE`.

CRUD implementado: **INSERT** (3 entidades), **SELECT** (listagens, busca por TAG e relatório com `JOIN` nas 3 tabelas) e **UPDATE** (equipamento e medição; na medição o status é recalculado antes de gravar).

## 5. Tratamento de erros SQL

- `sqlite3.IntegrityError` (TAG/matrícula duplicada, FK inválida) → `rollback` + `ErroBanco("Violacao de integridade...")`.
- Qualquer outro `sqlite3.Error` → `rollback` + `ErroBanco("Erro SQL...")`.
- Erro de conexão no construtor também vira `ErroBanco`.
- Dados inválidos (nome vazio, tolerância negativa) são barrados antes de chegar no banco, com `ValueError`.
- No `main`, tudo fica num `try/except/finally`, e a conexão sempre é fechada.

## 6. Validação do fluxo funcional

Rodamos `python 05_main.py` e o fluxo completo funcionou. Saída resumida:

```
Inserida: Medicao ref=100.0 obtido=100.02 tol=±0.05 -> APROVADO
Inserida: Medicao ref=5.0 obtido=5.15 tol=±0.1 -> REPROVADO
Inserida: Medicao ref=25.0 obtido=24.9 tol=±0.2 -> APROVADO

=== Relatorio de calibracao (antes do UPDATE) ===
ID  DATA        TAG      EQUIPAMENTO         TECNICO       REF     OBT    TOL  STATUS
1   2026-10-20  PAQ-01   Paquimetro 150mm    Carlos Silva  100.00  100.02 0.05 APROVADO
2   2026-10-21  MAN-07   Manometro 0-10 bar  Ana Souza       5.00    5.15 0.10 REPROVADO
3   2026-10-22  TRM-03   Termometro digital  Carlos Silva   25.00   24.90 0.20 APROVADO

=== Relatorio de calibracao (depois do UPDATE) ===
2   2026-10-21  MAN-07   Manometro 0-10 bar  Ana Souza       5.00    5.04 0.10 APROVADO

=== Teste de tratamento de erro (TAG duplicada) ===
Erro tratado direitinho -> Violacao de integridade: UNIQUE constraint failed: equipamentos.codigo_tag
```

| Teste | Resultado esperado | Resultado |
|---|---|---|
| Inserção de técnicos, equipamentos e medições | Registros gravados com IDs gerados | OK |
| Status calculado (erro 0,15 > tol. 0,10) | `REPROVADO` | OK |
| UPDATE do valor obtido (5,04) | Status recalculado pra `APROVADO` | OK |
| JOIN nas 3 tabelas | Relatório com TAG, técnico e status | OK |
| TAG duplicada | `ErroBanco` tratado, sem travar | OK |

## 7. Como rodar

```bash
python 05_main.py
```
Os dois arquivos precisam estar na mesma pasta. O `05_main.py` usa `importlib` pra importar o `04_classes.py`, já que nome de módulo começando com número não funciona com `import` normal. O banco `calibracao_teste.db` é recriado a cada execução.
