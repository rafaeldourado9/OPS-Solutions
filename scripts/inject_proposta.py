"""
Comprehensive injection of PROPOSTA.docx — creates PROPOSTA_TEMPLATE.docx
with all variable fields replaced by {placeholder} syntax.

Run:  python3 D:/CRM/scripts/inject_proposta.py
"""
from docx import Document
from docx.oxml.ns import qn
from lxml import etree
import io, copy, re

DOCX_IN  = 'D:/CRM/PROPOSTA.docx'
DOCX_OUT = 'D:/CRM/PROPOSTA_TEMPLATE.docx'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


# ── helpers ───────────────────────────────────────────────────────────────────

def para_text(elem):
    return ''.join(
        t.text or ''
        for run in elem.findall(f'{{{W}}}r')
        for t in run.findall(f'{{{W}}}t')
    )


def replace_text_in_para(para_elem, pattern: str, replacement: str):
    """Replace first occurrence of `pattern` with `replacement` in paragraph,
    preserving run formatting of the first run that contains the pattern start."""
    runs = para_elem.findall(f'{{{W}}}r')
    if not runs:
        return False

    # Build char→(run, t_elem) map
    char_map = []
    for run in runs:
        for t in run.findall(f'{{{W}}}t'):
            for ch in (t.text or ''):
                char_map.append((ch, run, t))

    full = ''.join(c[0] for c in char_map)
    idx = full.find(pattern)
    if idx == -1:
        return False

    end = idx + len(pattern)
    new_full = full[:idx] + replacement + full[end:]

    # Redistribute: put everything into first run first t-elem, blank the rest
    if char_map:
        first_run, first_t = char_map[0][1], char_map[0][2]
    else:
        return False

    first_t.text = new_full
    if new_full and (new_full[0] == ' ' or new_full[-1] == ' '):
        first_t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

    # Blank all other t-elems
    for _, run, t in char_map:
        if t is not first_t:
            t.text = ''

    return True


def replace_all_in_para(para_elem, replacements: list):
    """Apply multiple (pattern, replacement) pairs sequentially."""
    runs = para_elem.findall(f'{{{W}}}r')
    if not runs:
        return

    char_map = []
    for run in runs:
        for t in run.findall(f'{{{W}}}t'):
            for ch in (t.text or ''):
                char_map.append((ch, run, t))

    full = ''.join(c[0] for c in char_map)
    modified = full
    for pattern, replacement in replacements:
        modified = modified.replace(pattern, replacement)

    if modified == full:
        return

    if char_map:
        first_t = char_map[0][2]
        first_t.text = modified
        if modified and (modified[0] == ' ' or modified[-1] == ' '):
            first_t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        for _, run, t in char_map:
            if t is not first_t:
                t.text = ''


def set_cell_text(cell_elem, text: str):
    """Replace the entire text content of a table cell."""
    for para in cell_elem.findall(f'.//{{{W}}}p'):
        runs = para.findall(f'{{{W}}}r')
        if not runs:
            continue
        char_map = []
        for run in runs:
            for t in run.findall(f'{{{W}}}t'):
                for ch in (t.text or ''):
                    char_map.append((ch, run, t))
        if not char_map:
            continue
        first_t = char_map[0][2]
        first_t.text = text
        for _, _, t in char_map:
            if t is not first_t:
                t.text = ''
        return True
    return False


def get_cell_text(cell) -> str:
    return ''.join(
        t.text or ''
        for t in cell._tc.iter(f'{{{W}}}t')
    ).strip()


# ── main injections ───────────────────────────────────────────────────────────

with open(DOCX_IN, 'rb') as f:
    data = f.read()

doc = Document(io.BytesIO(data))

# Replacements applied globally across all paragraphs (longest first)
GLOBAL_REPLACEMENTS = [
    # Cover
    ("Nome do cliente",                      "{nome_cliente}"),
    ("0,00 kwp",                             "{potencia_kwp}"),

    # Additional data — inline values
    ("92%",                                  "{economia_percentual}"),
    ("20/02/2026",                           "{data_criacao}"),
    ("7 dias",                               "{validade_dias}"),

    # Dimensioning
    ("0.0 kWp",                              "{potencia_instalada_kwp}"),
    ("000W (consultar disponibilidade)",      "{potencia_placa_w}"),
    ("00 m\u00b2",                           "{area_m2}"),

    # Equipment names (longer → matched before '000W')
    ("M\u00d3DULO TSUN 000W",               "{modelo_modulo}"),
    ("INVERSOR SAJ 0000 W",                  "{modelo_inversor}"),
    ("INVERSOR SAJ 0000W",                   "{modelo_inversor}"),

    # Generation — same key for both occurrences (requerida & estimada)
    ("000 kW",                               "{geracao_kw}"),

    # Financial
    ("R$ 0.000,00",                          "{valor_total}"),

    # Signature
    ("NOME DO CLIENTE",                      "{nome_cliente}"),
]

# Sort longest-first so "MÓDULO TSUN 000W" matches before "000W"
GLOBAL_REPLACEMENTS.sort(key=lambda x: len(x[0]), reverse=True)

# 1. Process all paragraphs (including inside tables)
injected_paras = 0
for para_elem in doc.element.body.iter(f'{{{W}}}p'):
    old = para_text(para_elem)
    replace_all_in_para(para_elem, GLOBAL_REPLACEMENTS)
    new = para_text(para_elem)
    if old != new:
        injected_paras += 1

print(f"Paragraph injections: {injected_paras}")

# 2. Fix "Quantidade de placas: 0" — inject only the trailing value
#    After global pass this may already be partially processed
for para_elem in doc.element.body.iter(f'{{{W}}}p'):
    t = para_text(para_elem).strip()
    if 'Quantidade de placas:' in t and '{' not in t:
        # Replace the trailing ' 0' with ' {qtd_placas}'
        replace_all_in_para(para_elem, [('Quantidade de placas: 0', 'Quantidade de placas: {qtd_placas}')])
        print(f"  Fixed qtd_placas: {repr(para_text(para_elem))}")

# 3. Client info section — paragraphs that are just labels with no values
#    Add placeholder text after each label
CLIENT_FIELD_MAP = {
    'Nome/Raz\u00e3oSocial:':  'Nome/Razão Social: {nome_razao_social}',
    'Endere\u00e7o:':          ' Endereço: {endereco}',
    'Bairro:':                  'Bairro: {bairro}',
    'Cidade:':                  'Cidade: {cidade}',
    'Estado:':                  ' Estado: {estado}',
}

for para_elem in doc.element.body.iter(f'{{{W}}}p'):
    t = para_text(para_elem).strip()
    # The paragraph has combined label text e.g. "Nome/RazãoSocial: Endereço:"
    if 'Nome/Raz' in t and 'Endere' in t and '{' not in t:
        replace_all_in_para(para_elem, [
            (t, 'Nome/Razão Social: {nome_razao_social}   Endereço: {endereco}')
        ])
        print(f"  Fixed client name+addr: {repr(para_text(para_elem))}")
    elif t == 'Bairro:' or t == 'Bairro:\xa0' :
        replace_all_in_para(para_elem, [(t, 'Bairro: {bairro}')])
        print(f"  Fixed bairro: {repr(para_text(para_elem))}")
    elif 'Cidade:' in t and 'Estado:' in t and '{' not in t:
        replace_all_in_para(para_elem, [(t, 'Cidade: {cidade}   Estado: {estado}')])
        print(f"  Fixed cidade+estado: {repr(para_text(para_elem))}")

# 4. Table: inject module/inverter quantities
for table in doc.tables:
    for row in table.rows:
        cells = row.cells
        if len(cells) < 2:
            continue
        c0 = get_cell_text(cells[0])
        c1 = get_cell_text(cells[1])

        if '{modelo_modulo}' in c0 and c1 == '0':
            set_cell_text(cells[1]._tc, '{qtd_modulos}')
            print(f"  Table: qtd_modulos injected (row: {c0[:30]})")
        elif '{modelo_inversor}' in c0 and c1 == '0':
            set_cell_text(cells[1]._tc, '{qtd_inversores}')
            print(f"  Table: qtd_inversores injected (row: {c0[:30]})")

# ── save & report ─────────────────────────────────────────────────────────────

buf = io.BytesIO()
doc.save(buf)
out_bytes = buf.getvalue()

with open(DOCX_OUT, 'wb') as f:
    f.write(out_bytes)

# Count final placeholders
import re as _re
all_text = ' '.join(
    t.text or ''
    for t in doc.element.body.iter(f'{{{W}}}t')
)
found = sorted(set(_re.findall(r'\{(\w+)\}', all_text)))
print(f"\n=== FINAL TEMPLATE: {len(found)} unique placeholders ===")
for k in found:
    print(f"  {{{k}}}")

print(f"\nSaved to: {DOCX_OUT}")
