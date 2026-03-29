"""Analyze PROPOSTA.docx and preview all placeholder injections."""
from docx import Document
from lxml import etree
import io

DOCX_PATH = 'D:/CRM/PROPOSTA.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

with open(DOCX_PATH, 'rb') as f:
    data = f.read()

doc = Document(io.BytesIO(data))

# Comprehensive injection map — ordered by specificity
INJECTIONS = {
    # Cover page
    "Nome do cliente":                      "nome_cliente",
    "0,00 kwp":                             "potencia_kwp",

    # Additional data (values only, not labels)
    "92%":                                  "economia_percentual",
    "20/02/2026":                           "data_criacao",
    "7 dias":                               "validade_dias",

    # Dimensioning — equipment-specific sizing
    "0.0 kWp":                              "potencia_instalada_kwp",
    "000W (consultar disponibilidade)":     "potencia_placa_w",
    "00 m\u00b2":                           "area_m2",

    # Equipment model names (longer → matched first)
    "M\u00d3DULO TSUN 000W":               "modelo_modulo",
    "INVERSOR SAJ 0000 W":                  "modelo_inversor",
    "INVERSOR SAJ 0000W":                   "modelo_inversor",

    # Generation values — both occurrences use same key
    "000 kW":                               "geracao_kw",

    # Financial — both valor total table cell and proposta line
    "R$ 0.000,00":                          "valor_total",

    # Signature block
    "NOME DO CLIENTE":                      "nome_cliente",
}

sorted_inj = sorted(INJECTIONS.items(), key=lambda x: len(x[0]), reverse=True)

print("=== INJECTION PREVIEW ===\n")
found_keys = set()
for elem in doc.element.body.iter(f'{{{W}}}p'):
    runs = elem.findall(f'{{{W}}}r')
    full_text = ''.join(
        ch
        for run in runs
        for t in run.findall(f'{{{W}}}t')
        for ch in (t.text or '')
    ).strip()
    if not full_text:
        continue

    modified = full_text
    for orig, key in sorted_inj:
        modified = modified.replace(orig, '{' + key + '}')

    if modified != full_text:
        print(f"  IN:  {repr(full_text[:110])}")
        print(f"  OUT: {repr(modified[:110])}")
        for orig, key in sorted_inj:
            if orig in full_text:
                found_keys.add(key)
        print()

print(f"\n=== UNIQUE PLACEHOLDER KEYS ({len(found_keys)}) ===")
for k in sorted(found_keys):
    print(f"  {{{k}}}")
