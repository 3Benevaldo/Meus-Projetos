# Programa Feito com Uso da Inteligencia Artificial

import json
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional

ARQUIVO = Path("produtos.json")


# =========================
# Normalização e validações
# =========================
def remover_acentos(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def prefixo_da_categoria(categoria: str, tamanho: int = 4) -> str:
    """
    Usa a primeira palavra da categoria, sem acentos, em maiúsculo.
    Ex.: "Periféricos" -> "PERI"
         "Cabos e Adaptadores" -> "CABO"
    """
    cat = remover_acentos(categoria).strip().upper()
    cat = re.sub(r"[^A-Z0-9]+", " ", cat).strip()
    if not cat:
        return "CAT"
    primeira = cat.split()[0]
    return primeira[:tamanho] if len(primeira) >= tamanho else primeira.ljust(tamanho, "X")


def normalizar_sku(sku: str) -> str:
    return sku.strip().upper()


def validar_ncm(ncm: str) -> bool:
    ncm = ncm.strip()
    return ncm.isdigit() and len(ncm) == 8


def validar_gtin(gtin: str) -> bool:
    """
    GTIN/EAN opcional:
    - vazio OK
    - se preenchido: 8/12/13/14 dígitos (formatos comuns)
    """
    gtin = gtin.strip()
    if gtin == "":
        return True
    return gtin.isdigit() and len(gtin) in (8, 12, 13, 14)


def validar_origem(origem: int) -> bool:
    return 0 <= origem <= 8


# =========================
# JSON (carregar/salvar)
# =========================
def carregar() -> List[Dict]:
    if not ARQUIVO.exists():
        return []
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Aviso: produtos.json inválido/corrompido. Iniciando lista vazia.")
        return []


def salvar(produtos: List[Dict]) -> None:
    tmp = ARQUIVO.with_suffix(".tmp")
    tmp.write_text(json.dumps(produtos, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ARQUIVO)


def proximo_id(produtos: List[Dict]) -> int:
    return 1 if not produtos else max(int(p.get("id", 0)) for p in produtos) + 1


# =========================
# Busca e SKU automático
# =========================
def buscar_por_sku(produtos: List[Dict], sku: str) -> Optional[Dict]:
    alvo = normalizar_sku(sku)
    for p in produtos:
        if normalizar_sku(str(p.get("sku", ""))) == alvo:
            return p
    return None


def gerar_sku_por_categoria(produtos: List[Dict], categoria: str, largura: int = 6) -> str:
    pref = prefixo_da_categoria(categoria, tamanho=4)
    padrao = re.compile(rf"^{re.escape(pref)}-(\d+)$")

    numeros = []
    for p in produtos:
        sku_existente = normalizar_sku(str(p.get("sku", "")))
        m = padrao.match(sku_existente)
        if m:
            numeros.append(int(m.group(1)))

    proximo = (max(numeros) + 1) if numeros else 1
    candidato = f"{pref}-{proximo:0{largura}d}"

    # Garantia extra contra colisão (raro, mas seguro)
    while buscar_por_sku(produtos, candidato):
        proximo += 1
        candidato = f"{pref}-{proximo:0{largura}d}"

    return candidato


# =========================
# Helpers de input
# =========================
def ler_obrigatorio(msg: str) -> str:
    while True:
        s = input(msg).strip()
        if s:
            return s
        print("Campo obrigatório. Tente novamente.\n")


def ler_float_ge0(msg: str) -> float:
    while True:
        txt = input(msg).strip().replace(",", ".")
        try:
            v = float(txt)
            if v < 0:
                print("Valor deve ser >= 0.\n")
                continue
            return v
        except ValueError:
            print("Número inválido. Tente novamente.\n")


def ler_int_ge0(msg: str) -> int:
    while True:
        txt = input(msg).strip()
        try:
            v = int(txt)
            if v < 0:
                print("Valor deve ser >= 0.\n")
                continue
            return v
        except ValueError:
            print("Inteiro inválido. Tente novamente.\n")


def ler_ncm() -> str:
    while True:
        ncm = input("NCM (8 dígitos): ").strip()
        if validar_ncm(ncm):
            return ncm
        print("NCM inválido. Informe exatamente 8 dígitos numéricos.\n")


def ler_gtin() -> str:
    while True:
        gtin = input("GTIN/EAN (opcional, Enter para vazio): ").strip()
        if validar_gtin(gtin):
            return gtin
        print("GTIN/EAN inválido. Use 8/12/13/14 dígitos ou deixe vazio.\n")


def ler_origem() -> int:
    while True:
        try:
            origem = int(input("Origem (0 a 8): ").strip())
            if validar_origem(origem):
                return origem
        except ValueError:
            pass
        print("Origem inválida. Informe um número entre 0 e 8.\n")


# =========================
# Funcionalidades
# =========================
def listar(produtos: List[Dict], incluir_inativos: bool = False) -> None:
    titulo = "TODOS (ativos e inativos)" if incluir_inativos else "ATIVOS"
    print(f"\n=== Lista de Produtos: {titulo} ===")

    if not produtos:
        print("Nenhum produto cadastrado.\n")
        return

    print("SKU           | Nome                         | Categoria       | NCM      | Preço     | Estoque | Status")
    print("-" * 105)

    exibiu = False
    for p in produtos:
        ativo = bool(p.get("ativo", True))
        if (not incluir_inativos) and (not ativo):
            continue

        sku = str(p.get("sku", ""))
        nome = str(p.get("nome", ""))
        cat = str(p.get("categoria", ""))
        ncm = str(p.get("ncm", ""))
        preco = float(p.get("preco_venda", 0.0))
        estoque = int(p.get("estoque", 0))
        status = "ATIVO" if ativo else "INATIVO"

        print(f"{sku:<13} | {nome:<28} | {cat:<14} | {ncm:<8} | {preco:>8.2f} | {estoque:>7} | {status:<7}")
        exibiu = True

    if not exibiu:
        print("(Nenhum produto para exibir com esse filtro.)")
    print()


def adicionar(produtos: List[Dict]) -> None:
    print("\n=== Adicionar Produto ===")
    nome = ler_obrigatorio("Nome do produto: ")
    categoria = ler_obrigatorio("Categoria: ")
    marca = ler_obrigatorio("Marca: ")
    fornecedor = ler_obrigatorio("Fornecedor: ")
    unidade = ler_obrigatorio("Unidade (ex.: UN, CX, KG): ")

    ncm = ler_ncm()
    gtin = ler_gtin()
    origem = ler_origem()

    preco_venda = ler_float_ge0("Preço de venda: ")
    preco_custo = ler_float_ge0("Preço de custo (0 se não tiver): ")
    estoque = ler_int_ge0("Estoque: ")

    sku = gerar_sku_por_categoria(produtos, categoria, largura=6)
    print(f"SKU gerado automaticamente: {sku}")

    novo = {
        "id": proximo_id(produtos),
        "sku": sku,
        "nome": nome,
        "categoria": categoria,
        "marca": marca,
        "fornecedor": fornecedor,
        "unidade": unidade,
        "ncm": ncm,
        "gtin_ean": gtin,
        "origem": origem,
        "preco_venda": preco_venda,
        "preco_custo": preco_custo,
        "estoque": estoque,
        "ativo": True,
    }

    produtos.append(novo)
    salvar(produtos)
    print("Produto cadastrado com sucesso.\n")


def atualizar(produtos: List[Dict]) -> None:
    print("\n=== Atualizar Produto (por SKU; SKU fixo) ===")
    sku = input("Informe o SKU do produto: ").strip()
    p = buscar_por_sku(produtos, sku)
    if not p:
        print("Produto não encontrado.\n")
        return

    print(f'SKU: {p.get("sku")} (fixo, não altera)')
    print("Deixe em branco para manter o valor atual.\n")

    # Campos texto
    nome = input(f'Nome ({p.get("nome","")}): ').strip()
    categoria = input(f'Categoria ({p.get("categoria","")}): ').strip()
    marca = input(f'Marca ({p.get("marca","")}): ').strip()
    fornecedor = input(f'Fornecedor ({p.get("fornecedor","")}): ').strip()
    unidade = input(f'Unidade ({p.get("unidade","")}): ').strip()

    if nome:
        p["nome"] = nome
    if categoria:
        p["categoria"] = categoria  # SKU NÃO muda
    if marca:
        p["marca"] = marca
    if fornecedor:
        p["fornecedor"] = fornecedor
    if unidade:
        p["unidade"] = unidade

    # Fiscal
    ncm = input(f'NCM ({p.get("ncm","")}): ').strip()
    if ncm:
        if not validar_ncm(ncm):
            print("NCM inválido. Atualização cancelada.\n")
            return
        p["ncm"] = ncm

    gtin = input(f'GTIN/EAN ({p.get("gtin_ean","")}): ').strip()
    if gtin:
        if not validar_gtin(gtin):
            print("GTIN/EAN inválido. Atualização cancelada.\n")
            return
        p["gtin_ean"] = gtin

    origem_txt = input(f'Origem ({p.get("origem","")}): ').strip()
    if origem_txt:
        try:
            origem = int(origem_txt)
        except ValueError:
            print("Origem inválida. Atualização cancelada.\n")
            return
        if not validar_origem(origem):
            print("Origem inválida (0 a 8). Atualização cancelada.\n")
            return
        p["origem"] = origem

    # Números
    pv_txt = input(f'Preço venda ({float(p.get("preco_venda",0.0)):.2f}): ').strip()
    if pv_txt:
        try:
            pv = float(pv_txt.replace(",", "."))
            if pv < 0:
                raise ValueError
            p["preco_venda"] = pv
        except ValueError:
            print("Preço de venda inválido. Atualização cancelada.\n")
            return

    pc_txt = input(f'Preço custo ({float(p.get("preco_custo",0.0)):.2f}): ').strip()
    if pc_txt:
        try:
            pc = float(pc_txt.replace(",", "."))
            if pc < 0:
                raise ValueError
            p["preco_custo"] = pc
        except ValueError:
            print("Preço de custo inválido. Atualização cancelada.\n")
            return

    est_txt = input(f'Estoque ({int(p.get("estoque",0))}): ').strip()
    if est_txt:
        try:
            est = int(est_txt)
            if est < 0:
                raise ValueError
            p["estoque"] = est
        except ValueError:
            print("Estoque inválido. Atualização cancelada.\n")
            return

    salvar(produtos)
    print("Produto atualizado com sucesso.\n")


def desativar(produtos: List[Dict]) -> None:
    print("\n=== Desativar Produto (soft delete) ===")
    sku = input("Informe o SKU do produto: ").strip()
    p = buscar_por_sku(produtos, sku)
    if not p:
        print("Produto não encontrado.\n")
        return

    if not p.get("ativo", True):
        print("Este produto já está desativado.\n")
        return

    conf = input(f'Deseja desativar "{p.get("nome")}" (SKU {p.get("sku")})? (s/n): ').strip().lower()
    if conf != "s":
        print("Operação cancelada.\n")
        return

    p["ativo"] = False
    salvar(produtos)
    print("Produto desativado com sucesso.\n")


# =========================
# Menu
# =========================
def main() -> None:
    produtos = carregar()

    while True:
        print("=== Sistema de Cadastro de Produtos (JSON + Validações) ===")
        print("1) Listar produtos (ativos)")
        print("2) Listar produtos (todos, incluindo inativos)")
        print("3) Adicionar produto (SKU automático por categoria)")
        print("4) Atualizar produto (por SKU; SKU fixo)")
        print("5) Desativar produto (soft delete; por SKU)")
        print("0) Sair")

        op = input("Escolha: ").strip()

        if op == "1":
            listar(produtos, incluir_inativos=False)
        elif op == "2":
            listar(produtos, incluir_inativos=True)
        elif op == "3":
            adicionar(produtos)
        elif op == "4":
            atualizar(produtos)
        elif op == "5":
            desativar(produtos)
        elif op == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.\n")


if __name__ == "__main__":
    main()