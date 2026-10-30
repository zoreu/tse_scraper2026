
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# TSE - ELEIÇÕES 2026 - SEGUNDO TURNO
# ==========================================

BASE = "https://resultados.tse.jus.br/oficial/ele2026/6258/dados"

ESTADOS = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins"
}

CANDIDATOS = {
    "13": "Lula",
    "22": "Flávio Bolsonaro"
}


def baixar_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=30) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def extrair_candidatos(dados):
    votos = {"13": 0, "22": 0}

    def percorrer(obj):
        if isinstance(obj, dict):
            # Candidato presidencial
            if obj.get("n") in votos and "vap" in obj:
                votos[obj["n"]] += int(obj["vap"] or 0)

            for valor in obj.values():
                percorrer(valor)

        elif isinstance(obj, list):
            for item in obj:
                percorrer(item)

    # Procura os candidatos dentro da estrutura da API
    for cargo in dados.get("carg", []):
        percorrer(cargo)

    return votos


def consultar_estado(sigla):
    uf = sigla.lower()

    url = (
        f"{BASE}/{uf}/"
        f"{uf}-c0001-e006258-u.json"
    )

    dados = baixar_json(url)
    votos = extrair_candidatos(dados)

    return {
        "sigla": sigla,
        "estado": ESTADOS[sigla],
        "lula": votos["13"],
        "flavio": votos["22"]
    }


def formatar(numero):
    return f"{numero:,}".replace(",", ".")


def main():
    print("=" * 65)
    print(" ELEIÇÕES PRESIDENCIAIS 2026 - SEGUNDO TURNO")
    print(" Fonte: API oficial do Tribunal Superior Eleitoral")
    print("=" * 65)

    resultados = []

    print("\nConsultando os 27 estados...\n")

    # Consultas paralelas para acelerar a coleta
    with ThreadPoolExecutor(max_workers=5) as executor:
        tarefas = {
            executor.submit(consultar_estado, uf): uf
            for uf in ESTADOS
        }

        for tarefa in as_completed(tarefas):
            uf = tarefas[tarefa]
            try:
                resultado = tarefa.result()
                resultados.append(resultado)
                print(f"[OK] {uf} - {resultado['estado']}")
            except Exception as erro:
                print(f"[ERRO] {uf}: {erro}")

    resultados.sort(key=lambda x: x["estado"])

    if len(resultados) != 27:
        print("\nATENÇÃO: Nem todos os estados foram consultados.")
        print(f"Estados obtidos: {len(resultados)}/27")
        return

    lula_estados = []
    flavio_estados = []

    soma_lula = 0
    soma_flavio = 0

    # Classificação dos estados
    for r in resultados:
        if r["lula"] > r["flavio"]:
            lula_estados.append(r)
            soma_lula += r["lula"]
        elif r["flavio"] > r["lula"]:
            flavio_estados.append(r)
            soma_flavio += r["flavio"]

    # Exibição dos resultados
    def mostrar_lista(titulo, lista, candidato):
        print("\n" + "=" * 65)
        print(titulo)
        print("=" * 65)

        for r in lista:
            votos = r[candidato]
            print(
                f"{r['sigla']:3} | "
                f"{r['estado']:<25} | "
                f"{formatar(votos):>12} votos"
            )

        print("-" * 65)
        print(f"Quantidade de estados: {len(lista)}")

    mostrar_lista(
        "ESTADOS VENCIDOS POR LULA",
        lula_estados,
        "lula"
    )

    mostrar_lista(
        "ESTADOS VENCIDOS POR FLÁVIO BOLSONARO",
        flavio_estados,
        "flavio"
    )

    # Soma dos votos nos estados vencidos
    print("\n" + "=" * 65)
    print("SOMA DOS VOTOS NOS ESTADOS VENCIDOS")
    print("=" * 65)

    print(f"Lula:           {formatar(soma_lula)} votos")
    print(f"Flávio:         {formatar(soma_flavio)} votos")

    print("\n" + "=" * 65)
    print("TOTAL NACIONAL - ARQUIVO OFICIAL DO TSE")
    print("=" * 65)

    url_brasil = (
        f"{BASE}/br/"
        "br-c0001-e006258-u.json"
    )

    dados_brasil = baixar_json(url_brasil)
    total_nacional = extrair_candidatos(dados_brasil)

    total_lula = total_nacional["13"]
    total_flavio = total_nacional["22"]

    print(f"Lula:           {formatar(total_lula)} votos")
    print(f"Flávio:         {formatar(total_flavio)} votos")

    diferenca = abs(total_lula - total_flavio)

    print(f"\nDiferença:      {formatar(diferenca)} votos")

    if total_lula > total_flavio:
        print("\nResultado nacional: Lula recebeu mais votos.")
    elif total_flavio > total_lula:
        print("\nResultado nacional: Flávio recebeu mais votos.")
    else:
        print("\nResultado nacional: empate.")

    # Conferência da soma dos estados
    print("\n" + "=" * 65)
    print("CONFERÊNCIA DOS DADOS")
    print("=" * 65)

    print(f"Soma Lula (27 UFs):   {formatar(sum(r['lula'] for r in resultados))}")
    print(f"Soma Flávio (27 UFs): {formatar(sum(r['flavio'] for r in resultados))}")

    print("\nConsulta concluída.")
    print("Fonte: https://resultados.tse.jus.br/")


if __name__ == "__main__":
    main()
