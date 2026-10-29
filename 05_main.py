"""
05_main.py - AV 03 (Projeto Aplicado I - Schulz S.A.)
Demonstracao do MVP: cria o banco, insere dados de teste, faz um UPDATE,
roda a consulta com JOIN e imprime o relatorio de calibracao.
"""
import importlib
import os

# o nome do arquivo comeca com numero, entao nao da pra usar "import" normal
cls = importlib.import_module("04_classes")
Tecnico, Equipamento, Medicao = cls.Tecnico, cls.Equipamento, cls.Medicao
BancoDados, ErroBanco = cls.BancoDados, cls.ErroBanco


def imprimir_relatorio(linhas):
    print(f"{'ID':<3} {'DATA':<11} {'TAG':<8} {'EQUIPAMENTO':<22} {'TECNICO':<14} "
          f"{'REF':>7} {'OBT':>7} {'TOL':>6}  STATUS")
    print("-" * 95)
    for r in linhas:
        print(f"{r['id_medicao']:<3} {r['data_medicao']:<11} {r['codigo_tag']:<8} "
              f"{r['descricao']:<22} {r['tecnico']:<14} {r['valor_referencia']:>7.2f} "
              f"{r['valor_obtido']:>7.2f} {r['tolerancia']:>6.2f}  {r['status']}")


def main():
    if os.path.exists("calibracao_teste.db"):
        os.remove("calibracao_teste.db")  # começa sempre do zero na demo

    banco = BancoDados("calibracao_teste.db")
    try:
        banco.criar_tabelas()

        # --- técnicos e equipamentos de teste ---
        t1 = Tecnico("T001", "Carlos Silva", "Metrologia")
        t2 = Tecnico("T002", "Ana Souza", "Laboratorio")
        for t in (t1, t2):
            banco.inserir_tecnico(t)

        e1 = Equipamento("PAQ-01", "Paquimetro 150mm", "Mitutoyo")
        e2 = Equipamento("MAN-07", "Manometro 0-10 bar", "Wika")
        e3 = Equipamento("TRM-03", "Termometro digital", "Incoterm")
        for e in (e1, e2, e3):
            banco.inserir_equipamento(e)

        # --- medições (status é calculado automaticamente) ---
        medicoes = [
            Medicao(e1.id_equipamento, t1.id_tecnico, 100.00, 100.02, 0.05, "2026-10-20"),
            Medicao(e2.id_equipamento, t2.id_tecnico, 5.00, 5.15, 0.10, "2026-10-21"),
            Medicao(e3.id_equipamento, t1.id_tecnico, 25.00, 24.90, 0.20, "2026-10-22"),
        ]
        for m in medicoes:
            banco.inserir_medicao(m)
            print("Inserida:", m)

        print("\n=== Relatorio de calibracao (antes do UPDATE) ===")
        imprimir_relatorio(banco.relatorio_calibracao())

        # --- UPDATE: refazendo a medição reprovada do manômetro ---
        m_reprovada = medicoes[1]
        m_reprovada.valor_obtido = 5.04  # recalibrado
        banco.atualizar_medicao(m_reprovada)

        print("\n=== Relatorio de calibracao (depois do UPDATE) ===")
        imprimir_relatorio(banco.relatorio_calibracao())

        # --- teste de erro SQL: TAG duplicada ---
        print("\n=== Teste de tratamento de erro (TAG duplicada) ===")
        try:
            banco.inserir_equipamento(Equipamento("PAQ-01", "Outro paquimetro", "X"))
        except ErroBanco as erro:
            print("Erro tratado direitinho ->", erro)

    except ErroBanco as erro:
        print("Falha no MVP:", erro)
    finally:
        banco.fechar()


if __name__ == "__main__":
    main()
