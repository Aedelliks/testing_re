import re
import json


def clean_names_with_numbers(text):
    """
    Czyści tekst usuwając liczby pomiędzy imionami

    Przykłady:
    "PRZEMYSŁAW JAN 14 701 PRZEMYSŁAW LECH" -> "PRZEMYSŁAW JAN, PRZEMYSŁAW LECH"
    "PRZEMYSŁAW JAN 133 70 PRZEMYSŁAW LECH" -> "PRZEMYSŁAW JAN, PRZEMYSŁAW LECH"
    "PRZEMYSŁAW JAN 133 733 PRZEMYSŁAW LECH" -> "PRZEMYSŁAW JAN, PRZEMYSŁAW LECH"
    """
    if not text:
        return ""

    # Usuń "Strona X z Y" jeśli występuje
    text = re.sub(r'\s*Strona \d+ z \d+\s*', ' ', text)

    # Znajdź wszystkie fragmenty składające się z liter (polskie znaki też)
    # Wzorzec: jedna lub więcej liter, następnie opcjonalnie spacja i kolejne litery
    name_parts = re.findall(r'[A-ZĄĆĘŁŃÓŚŹŻ]+(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ]+)*', text, re.IGNORECASE)

    # Filtruj puste fragmenty i połącz przecinkami
    clean_names = [name.strip() for name in name_parts if name.strip()]

    return ', '.join(clean_names)

def extract_zarzad_info(text_content):
    """GŁÓWNA FUNKCJA EKSTRAKCJI DANYCH ZARZĄDU"""
    people_data = []

    # Początek i koniec sekcji
    start_pattern = re.compile(
        r"Organ uprawniony do reprezentacji podmiotu",
        re.DOTALL
    )
    end_pattern = re.compile(r"Organ nadzoru", re.DOTALL)

    start_match = start_pattern.search(text_content)
    if not start_match:
        return people_data

    text_after_start = text_content[start_match.end():]
    end_match = end_pattern.search(text_after_start)
    relevant_section = text_after_start[:end_match.start()] if end_match else text_after_start

    # Bloki osób
    block_pattern = re.compile(
        r"(?P<blok>\d+\.\s*Nazwisko\s*/\s*Nazwa\s*lub\s*Firma(?:.*?))(?=\n\d+\.\s*Nazwisko\s*/\s*Nazwa\s*lub\s*Firma|$)",
        re.DOTALL
    )
    blocks = block_pattern.findall(relevant_section)

    # Oddzielne wzorce pól
field_patterns = {
    "nazwisko": re.compile(
        r"1\.Nazwisko\s*/\s*Nazwa\s*lub\s*Firma(?:.*\n){0,2}(?:\d+\s*\n)*"
        r"(?:-\s*\n)*([^\d\n]+)",  # dowolne litery (bez cyfr i nowej linii)
        re.UNICODE
    ),
    "imiona": re.compile(
        r"2\.Imiona(?:.*\n){0,2}(?:\d+\s*\n)*"
        r"(?:-\s*\n)*([^\d\n]+(?:\n(?:\d+\s*\n)*(?:-\s*\n)*[^\d\n]+)?)",
        re.UNICODE
    ),
    "pesel": re.compile(
        r"3\.Numer PESEL/REGON(?:.*\n){0,2}(?:\d+\s*\n)*"
        r"(?:-\s*\n)*([0-9,\- ]{5,})"
    ),
    "krs": re.compile(
        r"4\.Numer KRS(?:.*\n){0,2}(?:\d+\s*\n)*"
        r"(?:-\s*\n)*([A-Z0-9\-\* ]+)?"
    ),
    "funkcja": re.compile(
        r"5\.Funkcja(?:.*\n){0,2}(?:\d+\s*\n)*"
        r"(?:-\s*\n)*([^\d\n]+(?:\n(?:\d+\s*\n)*(?:-\s*\n)*[^\d\n]+)*)",
        re.UNICODE
    ),
    "zawieszona": re.compile(
        r"6\.Czy osoba(?:.*\n){0,2}(?:\d+\s*\n)*(?:-\s*\n)*(TAK|NIE)"
    ),
    "data": re.compile(
        r"7\.Data do jakiej(?:.*\n){0,2}(?:\d+\s*\n)*(?:-\s*\n)*([0-9\.\- ]{2,}|[-—])"
    ),
}

    for i, block in enumerate(blocks, start=1):
        person_dict = {
            "Lp": i,
            "Nazwisko": "",
            "Imiona": "",
            "PESEL_REGON_DataUrodzenia": "",
            "NumerKRS": "",
            "FunkcjaWOrganie": "",
            "CzyZawieszona": "",
            "DataZawieszenia": "",
        }

        for key, regex in field_patterns.items():
            match = regex.search(block)
            if match:
                value = match.group(1).replace("\n", " ").strip()
                if key == "nazwisko":
                    person_dict["Nazwisko"] = value
                elif key == "imiona":
                    person_dict["Imiona"] = value
                elif key == "pesel":
                    person_dict["PESEL_REGON_DataUrodzenia"] = value
                elif key == "krs":
                    person_dict["NumerKRS"] = value
                elif key == "funkcja":
                    person_dict["FunkcjaWOrganie"] = value
                elif key == "zawieszona":
                    person_dict["CzyZawieszona"] = value
                elif key == "data":
                    person_dict["DataZawieszenia"] = value

        people_data.append(person_dict)

    return people_data



# Wczytaj zawartość pliku tekstowego
# file_path = 'tekst_z_pdf.txt'
file_path = 'text_z_pdf_aktualny.txt'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    print(f"Błąd: Plik '{file_path}' nie został znaleziony.")
    exit()

# Wyekstrahuj informacje
zarzad_info = extract_zarzad_info(content)


all_extracted_data = {
        "zarzad": zarzad_info,

}

# Zapisz do pliku JSON
output_json_path = 'wszystkie_dane_osob.json'
with open(output_json_path, 'w', encoding='utf-8') as f_json:
    json.dump(all_extracted_data, f_json, indent=4, ensure_ascii=False)

print(f"Dane zostały wyekstrahowane i zapisane do pliku: {output_json_path}")
if not zarzad_info:
    print("Nie znaleziono żadnych danych osób w pliku. Sprawdź wzorce regex lub strukturę pliku.")
else:
    print(f"  Znaleziono {len(zarzad_info)} osób w zarządzie.")

