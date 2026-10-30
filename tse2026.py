
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================================
# ELEIÇÕES 2026 - PRESIDENTE - SEGUNDO TURNO
# Fonte: API oficial do TSE
# ==========================================================

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


# ==========================================================
# FUNÇÕES
# ==========================================================

def baixar_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=30) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def extrair_votos(dados):
    votos = {"13": 0, "22": 0}

    for cargo in dados.get("carg", []):
        for agregacao in cargo.get("agr", []):
            for partido in agregacao.get("par", []):
                for candidato in partido.get("cand", []):
                    numero = candidato.get("n")

                    if numero in votos:
                        votos[numero] += int(
                            candidato.get("vap") or 0
                        )

    return votos


def consultar_local(codigo, nome):
    codigo = codigo.lower()

    url = (
        f"{BASE}/{codigo}/"
        f"{codigo}-c0001-e006258-u.json"
    )

    dados = baixar_json(url)
    votos = extrair_votos(dados)

    return {
        "sigla": codigo.upper(),
        "estado": nome,
        "lula": votos["13"],
        "flavio": votos["22"]
    }


def formatar(valor):
    return f"{valor:,}".replace(",", ".")


# ==========================================================
# TABELA COMPARATIVA DOS ESTADOS
# ==========================================================

def mostrar_comparativo(titulo, lista):

    print("\n" + "=" * 105)
    print(titulo)
    print("=" * 105)

    print(
        f"{'UF':<5}"
        f"{'Estado':<25}"
        f"{'Votos Lula':>17}"
        f"{'Votos Flávio':>19}"
        f"{'Diferença':>17}"
        f"{'Vencedor':>17}"
    )

    print("-" * 105)

    total_lula = 0
    total_flavio = 0

    # Ordena pela votação do candidato derrotado
    lista = sorted(
        lista,
        key=lambda r: min(r["lula"], r["flavio"]),
        reverse=True
    )

    for r in lista:

        diferenca = abs(r["lula"] - r["flavio"])

        if r["lula"] > r["flavio"]:
            vencedor = "Lula"
        elif r["flavio"] > r["lula"]:
            vencedor = "Flávio"
        else:
            vencedor = "Empate"

        print(
            f"{r['sigla']:<5}"
            f"{r['estado']:<25}"
            f"{formatar(r['lula']):>17}"
            f"{formatar(r['flavio']):>19}"
            f"{formatar(diferenca):>17}"
            f"{vencedor:>17}"
        )

        total_lula += r["lula"]
        total_flavio += r["flavio"]

    print("-" * 105)

    print(
        f"{'TOTAL':<30}"
        f"{formatar(total_lula):>17}"
        f"{formatar(total_flavio):>19}"
        f"{formatar(abs(total_lula-total_flavio)):>17}"
    )

    print(f"\nQuantidade de estados: {len(lista)}")


# ==========================================================
# PROGRAMA PRINCIPAL
# ==========================================================

def main():

    print("=" * 80)
    print("ELEIÇÕES PRESIDENCIAIS 2026 - SEGUNDO TURNO")
    print("Fonte: Tribunal Superior Eleitoral")
    print("=" * 80)

    resultados = []

    # ------------------------------------------------------
    # CONSULTAR OS ESTADOS
    # ------------------------------------------------------

    print("\nConsultando os 27 estados...\n")

    with ThreadPoolExecutor(max_workers=5) as executor:

        tarefas = {
            executor.submit(
                consultar_local, uf, nome
            ): uf
            for uf, nome in ESTADOS.items()
        }

        for tarefa in as_completed(tarefas):

            uf = tarefas[tarefa]

            try:
                resultado = tarefa.result()
                resultados.append(resultado)

                print(f"[OK] {uf} - {ESTADOS[uf]}")

            except Exception as erro:
                print(f"[ERRO] {uf}: {erro}")

    if len(resultados) != 27:
        print("\nERRO: Consulta incompleta.")
        print(f"Estados consultados: {len(resultados)}/27")
        return

    resultados.sort(key=lambda x: x["estado"])

    # ------------------------------------------------------
    # CONSULTAR EXTERIOR
    # ------------------------------------------------------

    print("\nConsultando exterior...")

    try:
        exterior = consultar_local("zz", "Exterior")
        print("[OK] Exterior")

    except Exception as erro:
        print(f"[ERRO] Exterior: {erro}")
        return

    lula_exterior = exterior["lula"]
    flavio_exterior = exterior["flavio"]

    # ------------------------------------------------------
    # CLASSIFICAR ESTADOS
    # ------------------------------------------------------

    lula_estados = []
    flavio_estados = []

    lula_perdeu = []
    flavio_perdeu = []

    for r in resultados:

        if r["lula"] > r["flavio"]:
            lula_estados.append(r)
            flavio_perdeu.append(r)

        elif r["flavio"] > r["lula"]:
            flavio_estados.append(r)
            lula_perdeu.append(r)

    # ------------------------------------------------------
    # 1 - ESTADOS VENCIDOS POR LULA
    # ------------------------------------------------------

    mostrar_comparativo(
        "ESTADOS VENCIDOS POR LULA",
        lula_estados
    )

    # ------------------------------------------------------
    # 2 - ESTADOS PERDIDOS POR LULA
    # ------------------------------------------------------

    mostrar_comparativo(
        "ESTADOS PERDIDOS POR LULA",
        lula_perdeu
    )

    # ------------------------------------------------------
    # 3 - ESTADOS VENCIDOS POR FLÁVIO
    # ------------------------------------------------------

    mostrar_comparativo(
        "ESTADOS VENCIDOS POR FLÁVIO",
        flavio_estados
    )

    # ------------------------------------------------------
    # 4 - ESTADOS PERDIDOS POR FLÁVIO
    # ------------------------------------------------------

    mostrar_comparativo(
        "ESTADOS PERDIDOS POR FLÁVIO",
        flavio_perdeu
    )

    # ------------------------------------------------------
    # 5 - EXTERIOR
    # ------------------------------------------------------

    print("\n" + "=" * 80)
    print("VOTAÇÃO NO EXTERIOR")
    print("=" * 80)

    print(f"Lula:   {formatar(lula_exterior)} votos")
    print(f"Flávio: {formatar(flavio_exterior)} votos")

    # ------------------------------------------------------
    # 6 - RESUMO DOS ESTADOS
    # ------------------------------------------------------

    lula_vencidos = sum(r["lula"] for r in lula_estados)
    lula_perdidos = sum(r["lula"] for r in lula_perdeu)

    flavio_vencidos = sum(r["flavio"] for r in flavio_estados)
    flavio_perdidos = sum(r["flavio"] for r in flavio_perdeu)

    print("\n" + "=" * 80)
    print("RESUMO DA DISTRIBUIÇÃO DOS VOTOS")
    print("=" * 80)

    print("\nLULA:")
    print(f"Estados vencidos: {formatar(lula_vencidos)}")
    print(f"Estados perdidos: {formatar(lula_perdidos)}")
    print(f"Exterior:         {formatar(lula_exterior)}")
    print(f"Total:         {formatar(lula_vencidos + lula_perdidos + lula_exterior)}")


    print("\nFLÁVIO:")
    print(f"Estados vencidos: {formatar(flavio_vencidos)}")
    print(f"Estados perdidos: {formatar(flavio_perdidos)}")
    print(f"Exterior:         {formatar(flavio_exterior)}")
    print(f"Total:         {formatar(flavio_vencidos + flavio_perdidos + flavio_exterior)}")

    # ------------------------------------------------------
    # 7 - ESTADOS VENCIDOS + EXTERIOR
    # ------------------------------------------------------

    # lula_subtotal = lula_vencidos + lula_exterior
    # flavio_subtotal = flavio_vencidos + flavio_exterior

    # print("\n" + "=" * 80)
    # print("ESTADOS VENCIDOS + EXTERIOR")
    # print("=" * 80)

    # print(f"Lula:   {formatar(lula_subtotal)}")
    # print(f"Flávio: {formatar(flavio_subtotal)}")

    # ------------------------------------------------------
    # 8 - TOTAL NACIONAL
    # ------------------------------------------------------

    todos_lula = lula_vencidos + lula_perdidos + lula_exterior
    todos_flavio = flavio_vencidos + flavio_perdidos + flavio_exterior

    diferenca = abs(todos_lula - todos_flavio)

    print("\n" + "=" * 80)
    print("TOTAL NACIONAL - TODAS AS UFs + EXTERIOR")
    print("=" * 80)

    print(f"Lula:      {formatar(todos_lula)} votos")
    print(f"Flávio:    {formatar(todos_flavio)} votos")
    print(f"Diferença: {formatar(diferenca)} votos")

    if todos_lula > todos_flavio:
        print("\nMAIOR TOTAL DE VOTOS: LULA")

    elif todos_flavio > todos_lula:
        print("\nMAIOR TOTAL DE VOTOS: FLÁVIO BOLSONARO")

    else:
        print("\nEMPATE")

    # ------------------------------------------------------
    # 9 - CONFERÊNCIA
    # ------------------------------------------------------

    # print("\n" + "=" * 80)
    # print("CONFERÊNCIA DOS DADOS")
    # print("=" * 80)

    # print(
    #     f"Total UFs Lula:   "
    #     f"{formatar(sum(r['lula'] for r in resultados))}"
    # )

    # print(
    #     f"Total UFs Flávio: "
    #     f"{formatar(sum(r['flavio'] for r in resultados))}"
    # )

    # print(f"Exterior Lula:    {formatar(lula_exterior)}")
    # print(f"Exterior Flávio:  {formatar(flavio_exterior)}")

    print("\nFonte: https://resultados.tse.jus.br/")
    print("Consulta concluída.")


if __name__ == "__main__":
    main()
