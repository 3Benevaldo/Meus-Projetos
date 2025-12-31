# Programa Feito com Ajuda da Inteligencia Artificial

import json
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional

ARQUIVO = Path("produtos.json")


# =========================
# Normalização e validações
# =========================
def normalizar_texto(s: str) -> str:
    """Remove acentos e normaliza para ASCII básico."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


def prefixo_categoria(categoria: str, tamanho: int = 4) -> str:
    """
    Gera prefixo a partir da categoria.
    Ex.: "Periféricos" -> "PERI"
         "Cabos e Adaptadores" -> "CABO" (primeira palavra)
    """
    cat = normalizar_texto(categoria).strip().upper()
    cat = re.sub(r"[^A-Z0-9]+", " ", cat).strip()
    if not cat:
        return "CAT"
    primeira = cat.split()[0]
    # Preenche com X se a palavra for curta
    return primeira[:tamanho] if len(primeira) >= tamanho else primeira.ljust(tamanho, "X")


def normalizar_sku(sku: str) -> str:
    return sku.strip().upper()


def validar_ncm(ncm: str) -> bool:
    ncm = ncm.strip()
    return ncm.isdigit() and len(ncm) == 8


def validar_gtin(gtin: str) -> bool:
    """
    GTIN/EAN opcional.
    Se preenchido, aceita 8/12/13/14 dígitos (formatos comuns).
    """
    gtin = gtin.strip()
    if gtin == "":
        return True
    return gtin.isdigit() and len(gtin) in (8, 12, 13, 14)


def validar_origem(origem: int) -> bool:
    return 0 <= origem <= 8


# =========================
# Persistência em JSON
# =========================
def carregar() -> List[Dict]:
    if not ARQUIVO.exists():
        return []
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Aviso: produtos.json está inválido. Iniciando lista vazia.")
        return []


def salvar(produtos: List[Dict]) -> None:
    tmp = ARQUIVO.with_suffix(".tmp")
    tmp.write_text(json.dumps(produtos, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ARQUIVO)


def proximo_id(produtos: List[Dict]) -> int:
    return 1 if not produtos else max(int(p.get("id", 0)) for p in produtos) + 1


# =========================
# Busca e geração de SKU
# =========================
def buscar_por_sku(produtos: List[Dict], sku: str) -> Optional[Dict]:
    alvo = normalizar_sku(sku)
    for p in produtos:
        if normalizar_sku(str(p.get("sku", ""))) == alvo:
            return p
    return None


def gerar_sku_por_categoria(produtos: List[Dict], categoria: str, largura: int = 6) -> str:
    pref = prefixo_categoria(categoria, tamanho=4)
    padrao = re.compile(rf"^{re.escape(pref)}-(\d+)$")

    numeros = []
    for p in produtos:
        sku_existente = normalizar_sku(str(p.get("sku", "")))
        m = padrao.match(sku_existente)
        if m:
            numeros.append(int(m.group(1)))

    proximo = (max(numeros) + 1) if numeros else 1
    return f"{pref}-{proximo:0{largura}d}"


# =========================
# Leitura de dados (inputs)
# =========================
def ler_str_obrigatorio(msg: str) -> str:
    while True:
        s = input(msg).strip()
        if s:
            return s
        print("Campo obrigatório. Tente novamente.\n")


def ler_float_obrigatorio(msg: str) -> float:
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


def ler_int_obrigatorio(msg: str) -> int:
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


def ler_ncm_obrigatorio() -> str:
    while True:
        ncm = input("NCM (8 dígitos): ").strip()
        if validar_ncm(ncm):
            return ncm
        print("NCM inválido. Informe exatamente 8 dígitos numéricos.\n")


def ler_gtin_opcional() -> str:
    while True:
        gtin = input("GTIN/EAN (opcional, Enter para vazio): ").strip()
        if validar_gtin(gtin):
            return gtin
        print("GTIN/EAN inválido. Use 8/12/13/14 dígitos ou deixe vazio.\n")


def ler_origem_obrigatorio() -> int:
    while True:
        print("Origem (0 a 8):")
        print("  0 Nacional")
        print("  1 Estrangeira - importação direta")
        print("  2 Estrangeira - adquirida no mercado interno")
        print("  3 Nacional - conteúdo de importação > 40%")
        print("  4 Nacional - processos produtivos básicos")
        print("  5 Nacional - conteúdo de importação <= 40%")
        print("  6 Estrangeira - importação direta (sem similar nacional) [exemplo]")
        print("  7 Estrangeira - adquirida mercado interno (sem similar nacional) [exemplo]")
        print("  8 Nacional - conteúdo importação > 70%")
        try:
            origem = int(input("Informe a origem: ").strip())
            if validar_origem(origem):
                return origem
        except ValueError:
            pass
        print("Origem inválida. Informe um número entre 0 e 8.\n")


# =========================
# CRUD
# =========================
def listar(produtos: List[Dict]) -> None:
    if not produtos:
        print("\nNenhum produto cadastrado.\n")
        return

    print("\nSKU           | Nome                         | Categoria       | NCM      | Preço     | Estoque")
    print("-" * 95)
    for p in produtos:
        sku = str(p.get("sku", ""))
        nome = str(p.get("nome", ""))
        cat = str(p.get("categoria", ""))
        ncm = str(p.get("ncm", ""))
        preco = float(p.get("preco_venda", 0.0))
        estoque = int(p.get("estoque", 0))
        print(f"{sku:<13} | {nome:<28} | {cat:<14} | {ncm:<8} | {preco:>8.2f} | {estoque:>7}")
    print()


def adicionar(produtos: List[Dict]) -> None:
    print("\n=== Adicionar Produto (com campos fiscais) ===")
    nome = ler_str_obrigatorio("Nome do produto: ")
    categoria = ler_str_obrigatorio("Categoria: ")
    marca = ler_str_obrigatorio("Marca: ")
    fornecedor = ler_str_obrigatorio("Fornecedor: ")
    unidade = ler_str_obrigatorio("Unidade (ex.: UN, CX, KG): ")

    ncm = ler_ncm_obrigatorio()
    gtin = ler_gtin_opcional()
    origem = ler_origem_obrigatorio()

    preco_venda = ler_float_obrigatorio("Preço de venda: ")
    preco_custo = ler_float_obrigatorio("Preço de custo (use 0 se não tiver): ")
    estoque = ler_int_obrigatorio("Estoque: ")

    sku = gerar_sku_por_categoria(produtos, categoria, largura=6)
    # Garantia extra: se por algum motivo houver colisão (raro), incrementa até achar livre
    while buscar_por_sku(produtos, sku):
        # força próximo número no mesmo prefixo
        prefixo = sku.split("-")[0]
        padrao = re.compile(rf"^{re.escape(prefixo)}-(\d+)$")
        numeros = []
        for p in produtos:
            m = padrao.match(normalizar_sku(str(p.get("sku", ""))))
            if m:
                numeros.append(int(m.group(1)))
        proximo = (max(numeros) + 1) if numeros else 1
        sku = f"{prefixo}-{proximo:06d}"

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
    print("\n=== Atualizar Produto (SKU fixo) ===")
    sku = input("Informe o SKU do produto: ").strip()
    p = buscar_por_sku(produtos, sku)
    if not p:
        print("Produto não encontrado.\n")
        return

    print(f'SKU: {p.get("sku")} (fixo, não altera)')
    print("Deixe em branco para manter o valor atual.\n")

    nome = input(f'Nome ({p.get("nome","")}): ').strip()
    categoria = input(f'Categoria ({p.get("categoria","")}): ').strip()
    marca = input(f'Marca ({p.get("marca","")}): ').strip()
    fornecedor = input(f'Fornecedor ({p.get("fornecedor","")}): ').strip()
    unidade = input(f'Unidade ({p.get("unidade","")}): ').strip()

    ncm = input(f'NCM ({p.get("ncm","")}): ').strip()
    gtin = input(f'GTIN/EAN ({p.get("gtin_ean","")}): ').strip()
    origem_txt = input(f'Origem ({p.get("origem","")}): ').strip()

    preco_venda_txt = input(f'Preço venda ({float(p.get("preco_venda",0.0)):.2f}): ').strip()
    preco_custo_txt = input(f'Preço custo ({float(p.get("preco_custo",0.0)):.2f}): ').strip()
    estoque_txt = input(f'Estoque ({int(p.get("estoque",0))}): ').strip()

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

    if ncm:
        if not validar_ncm(ncm):
            print("NCM inválido. Atualização cancelada.\n")
            return
        p["ncm"] = ncm

    if gtin != "":
        # se usuário digitou algo, valida; se digitou vazio, zera (permite remover)
        if not validar_gtin(gtin):
            print("GTIN/EAN inválido. Atualização cancelada.\n")
            return
        p["gtin_ean"] = gtin

    if origem_txt:
        try:
            origem = int(origem_txt)
            if not validar_origem(origem):
                print("Origem inválida (0 a 8). Atualização cancelada.\n")
                return
            p["origem"] = origem
        except ValueError:
            print("Origem inválida. Atualização cancelada.\n")
            return

    if preco_venda_txt:
        try:
            pv = float(preco_venda_txt.replace(",", "."))
            if pv < 0:
                raise ValueError
            p["preco_venda"] = pv
        except ValueError:
            print("Preço de venda inválido. Atualização cancelada.\n")
            return

    if preco_custo_txt:
        try:
            pc = float(preco_custo_txt.replace(",", "."))
            if pc < 0:
                raise ValueError
            p["preco_custo"] = pc
        except ValueError:
            print("Preço de custo inválido. Atualização cancelada.\n")
            return

    if estoque_txt:
        try:
            est = int(estoque_txt)
            if est < 0:
                raise ValueError
            p["estoque"] = est
        except ValueError:
            print("Estoque inválido. Atualização cancelada.\n")
            return

    salvar(produtos)
    print("Produto atualizado com sucesso.\n")


def excluir(produtos: List[Dict]) -> None:
    print("\n=== Excluir Produto ===")
    sku = input("Informe o SKU do produto: ").strip()
    p = buscar_por_sku(produtos, sku)
    if not p:
        print("Produto não encontrado.\n")
        return

    conf = input(f'Confirma excluir "{p.get("nome")}" (SKU {p.get("sku")})? (s/n): ').strip().lower()
    if conf != "s":
        print("Exclusão cancelada.\n")
        return

    produtos.remove(p)
    salvar(produtos)
    print("Produto excluído com sucesso.\n")


def main() -> None:
    produtos = carregar()

    while True:
        print("=== Cadastro de Produtos (JSON + Fiscal) ===")
        print("1) Listar produtos")
        print("2) Adicionar produto (SKU automático por categoria)")
        print("3) Atualizar produto (por SKU, SKU fixo)")
        print("4) Excluir produto (por SKU)")
        print("0) Sair")
        op = input("Escolha: ").strip()

        if op == "1":
            listar(produtos)
        elif op == "2":
            adicionar(produtos)
        elif op == "3":
            atualizar(produtos)
        elif op == "4":
            excluir(produtos)
        elif op == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.\n")


if __name__ == "__main__":
    main()