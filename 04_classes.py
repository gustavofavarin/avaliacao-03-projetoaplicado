"""
04_classes.py - AV 03 (Projeto Aplicado I - Schulz S.A.)
Classes de dominio (Tecnico, Equipamento, Medicao) e classe de
conexao/persistencia (BancoDados) usando sqlite3.
"""
import sqlite3
from datetime import date


class ErroBanco(Exception):
    """Erro proprio pra encapsular qualquer problema vindo do SQLite."""


# ----------------------------------------------------------------------
# Classes de dominio
# ----------------------------------------------------------------------
class Tecnico:
    def __init__(self, matricula, nome, setor, id_tecnico=None):
        self.id_tecnico = id_tecnico
        self.matricula = matricula
        self.nome = nome
        self.setor = setor

    # encapsulamento: valida o que entra nos atributos principais
    @property
    def matricula(self):
        return self._matricula

    @matricula.setter
    def matricula(self, valor):
        valor = str(valor).strip()
        if not valor:
            raise ValueError("Matricula nao pode ficar vazia.")
        self._matricula = valor

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        valor = str(valor).strip()
        if not valor:
            raise ValueError("Nome do tecnico nao pode ficar vazio.")
        self._nome = valor

    def __str__(self):
        return f"Tecnico[{self.matricula}] {self.nome} ({self.setor})"


class Equipamento:
    def __init__(self, codigo_tag, descricao, fabricante, id_equipamento=None):
        self.id_equipamento = id_equipamento
        self.codigo_tag = codigo_tag
        self.descricao = descricao
        self.fabricante = fabricante

    @property
    def codigo_tag(self):
        return self._codigo_tag

    @codigo_tag.setter
    def codigo_tag(self, valor):
        valor = str(valor).strip().upper()
        if not valor:
            raise ValueError("Codigo TAG nao pode ficar vazio.")
        self._codigo_tag = valor

    def __str__(self):
        return f"Equipamento[{self.codigo_tag}] {self.descricao} - {self.fabricante}"


class Medicao:
    """Ensaio de calibracao. O status e calculado pela propria classe."""

    def __init__(self, id_equipamento, id_tecnico, valor_referencia,
                 valor_obtido, tolerancia, data_medicao=None, id_medicao=None):
        if tolerancia < 0:
            raise ValueError("Tolerancia nao pode ser negativa.")
        self.id_medicao = id_medicao
        self.id_equipamento = id_equipamento
        self.id_tecnico = id_tecnico
        self.valor_referencia = float(valor_referencia)
        self.valor_obtido = float(valor_obtido)
        self.tolerancia = float(tolerancia)
        self.data_medicao = data_medicao or date.today().isoformat()

    @property
    def erro(self):
        return abs(self.valor_obtido - self.valor_referencia)

    @property
    def status(self):
        # regra metrologica: erro absoluto tem que ficar dentro da tolerancia
        return "APROVADO" if self.erro <= self.tolerancia else "REPROVADO"

    def __str__(self):
        return (f"Medicao ref={self.valor_referencia} obtido={self.valor_obtido} "
                f"tol=±{self.tolerancia} -> {self.status}")


# ----------------------------------------------------------------------
# Conexao e persistencia
# ----------------------------------------------------------------------
class BancoDados:
    def __init__(self, caminho="calibracao.db"):
        try:
            self.conn = sqlite3.connect(caminho)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            raise ErroBanco(f"Nao consegui conectar no banco: {e}") from e

    def fechar(self):
        self.conn.close()

    def _executar(self, sql, params=()):
        """Ponto unico de execucao: commit se der certo, rollback se der erro."""
        try:
            cur = self.conn.execute(sql, params)
            self.conn.commit()
            return cur
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise ErroBanco(f"Violacao de integridade: {e}") from e
        except sqlite3.Error as e:
            self.conn.rollback()
            raise ErroBanco(f"Erro SQL: {e}") from e

    def criar_tabelas(self):
        self._executar("""CREATE TABLE IF NOT EXISTS tecnicos (
            id_tecnico INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula  TEXT NOT NULL UNIQUE,
            nome       TEXT NOT NULL,
            setor      TEXT)""")
        self._executar("""CREATE TABLE IF NOT EXISTS equipamentos (
            id_equipamento INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_tag     TEXT NOT NULL UNIQUE,
            descricao      TEXT NOT NULL,
            fabricante     TEXT)""")
        self._executar("""CREATE TABLE IF NOT EXISTS medicoes (
            id_medicao       INTEGER PRIMARY KEY AUTOINCREMENT,
            id_equipamento   INTEGER NOT NULL REFERENCES equipamentos(id_equipamento),
            id_tecnico       INTEGER NOT NULL REFERENCES tecnicos(id_tecnico),
            data_medicao     TEXT NOT NULL,
            valor_referencia REAL NOT NULL,
            valor_obtido     REAL NOT NULL,
            tolerancia       REAL NOT NULL,
            status           TEXT NOT NULL CHECK (status IN ('APROVADO','REPROVADO')))""")

    # ---------- INSERT ----------
    def inserir_tecnico(self, t):
        cur = self._executar(
            "INSERT INTO tecnicos (matricula, nome, setor) VALUES (?, ?, ?)",
            (t.matricula, t.nome, t.setor))
        t.id_tecnico = cur.lastrowid
        return t.id_tecnico

    def inserir_equipamento(self, e):
        cur = self._executar(
            "INSERT INTO equipamentos (codigo_tag, descricao, fabricante) VALUES (?, ?, ?)",
            (e.codigo_tag, e.descricao, e.fabricante))
        e.id_equipamento = cur.lastrowid
        return e.id_equipamento

    def inserir_medicao(self, m):
        cur = self._executar(
            """INSERT INTO medicoes (id_equipamento, id_tecnico, data_medicao,
               valor_referencia, valor_obtido, tolerancia, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (m.id_equipamento, m.id_tecnico, m.data_medicao,
             m.valor_referencia, m.valor_obtido, m.tolerancia, m.status))
        m.id_medicao = cur.lastrowid
        return m.id_medicao

    # ---------- SELECT ----------
    def listar_tecnicos(self):
        rows = self._executar("SELECT * FROM tecnicos ORDER BY nome").fetchall()
        return [Tecnico(r["matricula"], r["nome"], r["setor"], r["id_tecnico"]) for r in rows]

    def listar_equipamentos(self):
        rows = self._executar("SELECT * FROM equipamentos ORDER BY codigo_tag").fetchall()
        return [Equipamento(r["codigo_tag"], r["descricao"], r["fabricante"],
                            r["id_equipamento"]) for r in rows]

    def buscar_equipamento_por_tag(self, tag):
        r = self._executar("SELECT * FROM equipamentos WHERE codigo_tag = ?",
                           (tag.strip().upper(),)).fetchone()
        if r is None:
            return None
        return Equipamento(r["codigo_tag"], r["descricao"], r["fabricante"], r["id_equipamento"])

    def relatorio_calibracao(self):
        """SELECT relacional com JOIN nas 3 tabelas."""
        sql = """SELECT m.id_medicao, m.data_medicao, e.codigo_tag, e.descricao,
                        t.nome AS tecnico, m.valor_referencia, m.valor_obtido,
                        m.tolerancia, m.status
                 FROM medicoes m
                 JOIN equipamentos e ON e.id_equipamento = m.id_equipamento
                 JOIN tecnicos t     ON t.id_tecnico     = m.id_tecnico
                 ORDER BY m.data_medicao, m.id_medicao"""
        return self._executar(sql).fetchall()

    # ---------- UPDATE ----------
    def atualizar_equipamento(self, e):
        cur = self._executar(
            "UPDATE equipamentos SET descricao=?, fabricante=? WHERE id_equipamento=?",
            (e.descricao, e.fabricante, e.id_equipamento))
        return cur.rowcount > 0

    def atualizar_medicao(self, m):
        """Recalcula o status com os valores novos antes de gravar."""
        cur = self._executar(
            """UPDATE medicoes SET valor_obtido=?, tolerancia=?, status=?
               WHERE id_medicao=?""",
            (m.valor_obtido, m.tolerancia, m.status, m.id_medicao))
        return cur.rowcount > 0
