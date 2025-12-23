estoque = ()

def adicionar_produto():
    nome = input("nome do produto: ").strip()
    if nome in estoque:
        print("produto já existente no estoque. ") 
        return
    try:
        preco = float(input("preço do produto: "))
        quantidade = int(input("quantidade em estoque: "))
        estoque[nome] = {"preco": preco, "quantidade": quantidade}
        print(f"produto '{nome}' adicionado com sucesso.")
    except ValueError:
        print("erro ao adicionar produto. certifique-se de que o preço e a quantidade são números válidos.")


def atualizar_produto():
    nome = input("nome do produto a atualiza: ").strip()
    if nome not in estoque:
        print("produto nao encontrado. ")
        return
    try:
        preco = float(input("nova quantidade: "))
        quantidade = int(input("nona quantidade: "))
        estoque[nome] = {"preco": preco, "quantidade": quantidade}
        print("produto atualizado com sucesso!")
    except ValueError:
        print("erro: preço ou quantidade invalidos. ")


def excluir_produto():
    nome = input("nome do produto a excluir: ").strip()
    if nome in estoque:
        del estoque[nome]
        print("produto excluido com sucesso!")
    else:
        print("produto nao encontrado. ")

def visualizar_estoque():
    if not estoque:
        print("estoque vazio. ")
        return
    print("\n--- estoque atual ---")
    for nome, dados in estoque.items():
        print(f"produto: {nome} | preço: R${dados['preco']:.2f} | quantidade: {dados['quantidade']}")

def menu():
    while True:
        print("\n[1] adcionar produto")
        print("[2] atualizar produto")
        print("[3] excluir produto")
        print("[4] visualizar estoque")
        print("[5] sair")

        opcao = input("escolha uma opção: ").strip()

        if opcao == "1":
            adicionar_produto()
        elif opcao == "2":
            atualizar_produto()
        elif opcao == "3":
            excluir_produto()
        elif opcao == "4":
            visualizar_estoque()
        elif opcao == "5":
            print("saindo...")
            break
        else:
            print("opção invalida. tente novamente.")

 # Iniciar o Sistema
menu()          