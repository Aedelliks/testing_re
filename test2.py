import json
import re

patterns = {
    'nazwisko': re.compile(
        r"\d+\s+1\.Nazwisko / Nazwa lub Firma\s+(?:\d+)?\s*(?:\d*|-)?\s*(.*?)(?=\s*2\.Imiona)", re.DOTALL),

    'imiona': re.compile(
        r"2\.Imiona\s+(?:\d+)?\s*(?:\d*|-)?\s*(.*?)(?=\s*3\.Numer PESEL)", re.DOTALL),

    'pesel': re.compile(
        r"3\.Numer PESEL/REGON lub data\s+urodzenia\s+(?:\d+)?\s*(?:\d*|-)?\s*(.*?)(?=\s*4\.Numer KRS)", re.DOTALL),

    'funkcja': re.compile(
        r"5\.Funkcja w organie\s+reprezentującym\s+(?:\d+)?\s*(?:\d*|-)?\s*(.*?)(?=\s*6\.Czy osoba)", re.DOTALL),

    'zawieszona': re.compile(
        r"6\.Czy osoba wchodząca w skład\s+zarządu została zawieszona w\s+czynnościach\?\s+(?:\d+)?\s*(?:\d*|-)?\s*(NIE|TAK)",
        re.DOTALL)
}

def clean_text_with_regex(text: str) -> str:
    # Usuń dokładne dopasowanie: "Strona xxx z xxx"
    text = re.sub(r"Strona\s+\d{1,3}\s+z\s+\d{1,3}", "", text)

    # Usuń pojedyncze słowa "Strona xxx"
    text = re.sub(r"Strona\s+\d{1,3}", "", text)

    # Usuń pojedyncze słowa "z xxx"
    text = re.sub(r"\bz\s+\d{1,3}", "", text)

    # Usuń znaki nowej linii i ich kombinacje
    text = text.replace('\n', ' ').replace(' n', ' ').replace('n ', ' ')

    # Redukuj wielokrotne spacje do jednej
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def extract_zarzad_info(text_content):
    """GLOWNA, DZIALAJACA FUNKCJA"""
    people_data = []

    # Wzorzec do znalezienia początku sekcji osób w zarządzie
    start_pattern = re.compile(
            r"Organ uprawniony do reprezentacji podmiotu\s+L\.p\.\s+Numer i nazwa pola\s+Nr "
            r"wpisu\s+Zawartość\s+wprow\s*\.\s*wykr\.\s*1\s+1\.Nazwa organu uprawnionego do\s+reprezentowania podmiotu\s+\d+\s+-\s+ZARZĄD BANKU\s+2\.Sposób reprezentacji podmiotu.*?Podrubryka 1\s+Dane osób wchodzących w skład organu",
            re.DOTALL
    )

    # Wzorzec do znalezienia końca sekcji (początek Rubryki 2)
    end_pattern = re.compile(r"Organ nadzoru", re.DOTALL)

    start_match = start_pattern.search(text_content)
    if not start_match:
        return people_data

    text_after_start = text_content[start_match.end():]
    end_match = end_pattern.search(text_after_start)
    relevant_section = text_after_start[:end_match.start()] if end_match else text_after_start

    # Wzorzec do podziału na segmenty osób
    # Podział na osoby
    person_segments_pattern = re.compile(
        r"(\d+)\s+1\.Nazwisko\s*/\s*Nazwa\s*lub\s*Firma(.*?)(?=\d+\s+1\.Nazwisko\s*/\s*Nazwa\s*lub\s*Firma|Rubryka 2|Strona \d+ z \d+|$)",
        re.DOTALL
    )

    # Oddzielne regexy dla każdego pola
    field_patterns = {
            "nazwisko": re.compile(
                    r"1\.Nazwisko\s*/\s*Nazwa\s*lub\s*Firma(?:.*\n){0,2}(?:\d+\s*\n)*"
                    r"(?:-\s*\n)*([A-ZĄĆĘŁŃÓŚŹŻ \-]+)"
            ),
            "imiona": re.compile(
                    r"2\.Imiona(?:.*\n){0,2}(?:\d+\s*\n)*"
                    r"(?:-\s*\n)*([A-ZĄĆĘŁŃÓŚŹŻ \-]+(?:\n(?:\d+\s*\n)*(?:-\s*\n)*[A-ZĄĆĘŁŃÓŚŹŻ \-]+)?)"
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
                    r"(?:-\s*\n)*([A-ZĄĆĘŁŃÓŚŹŻ ,\.\-]+"
                    r"(?:\n(?:\d+\s*\n)*(?:-\s*\n)*[A-ZĄĆĘŁŃÓŚŹŻ ,\.\-]+)*)"
            ),
            "zawieszona": re.compile(
                    r"6\.Czy osoba(?:.*\n){0,2}(?:\d+\s*\n)*(?:-\s*\n)*(TAK|NIE)"
            ),
            "data": re.compile(
                    r"7\.Data do jakiej(?:.*\n){0,2}(?:\d+\s*\n)*(?:-\s*\n)*([0-9\.\- ]{2,}|[-—])"
            ),
    }

    for segment_match in person_segments_pattern.finditer(relevant_section):
        lp = segment_match.group(1).strip()
        segment_text = segment_match.group(2)

        person_dict = {
            "Lp": lp,
            "Nazwisko": "",
            "Imiona": "",
            "PESEL_REGON_DataUrodzenia": "",
            "NumerKRS": "",
            "FunkcjaWOrganie": "",
            "CzyZawieszona": "",
            "DataZawieszenia": "",
        }

        # Parsowanie każdego pola oddzielnie
        for key, regex in field_patterns.items():
            match = regex.search(segment_text)
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

def extract_nadzor_info(text_content):
    people_data = []
    start_pattern = re.compile(
            r"Rubryka 2 Organ nadzoru\s+L\.p\.\s+Numer i nazwa pola\s+Nr wpisu\s+Zawartość\s+wprow\s*\.\s*wykr\.\s*1\s+1\.Nazwa organu\s+\d+\s+-\s+RADA NADZORCZA\s+Podrubryka 1\s+Dane osób wchodzących w skład organu",
            re.DOTALL)
    end_pattern = re.compile(r"Rubryka 3 Prokurenci", re.DOTALL)

    start_match = start_pattern.search(text_content)
    if not start_match:
        return people_data

    text_after_start = text_content[start_match.end():]
    end_match = end_pattern.search(text_after_start)
    relevant_section = text_after_start[:end_match.start()] if end_match else text_after_start

    # Wzorzec dla osób w radzie nadzorczej
    # Pola: Lp, Nazwisko, Imiona, PESEL/DataUrodzenia
    # (Nr wpisu wprow i wykr są obecne, ale nie zawsze wypełnione dla PESEL)
    person_pattern_nadzor = re.compile(
    r"(\d+)\s+"  # L.p. osoby (grupa 1)
    r"1\.Nazwisko / Nazwa lub Firma\s+"
    r"(\d*)\s*(\d*|-)\s*([\S ]+?)\s+"  # Nr wpisu wprow, wykr, Nazwisko (grupy 2, 3, 4)
    r"2\.Imiona\s+"
    r"(\d*)\s*(\d*|-)\s*([\S ]+?)\s+"  # Nr wpisu wprow, wykr, Imiona (grupy 5, 6, 7)
    r"3\.Numer PESEL/REGON lub data\s+urodzenia\s+"
    r"(\d*)\s*(\d*|-)\s*([\S\s]+?)\s+"  # Nr wpisu wprow, wykr, PESEL/data (grupy 8, 9, 10)
    r"4\.Numer KRS\s+-\s+-\s+\*+\s+"
    r"5\.Funkcja w organie\s+reprezentującym\s+"
    # ZMODYFIKOWANA LINIA DLA FUNKCJI:
    r"(\d*)\s*(\d*|-)\s*([\S\s]+?)\s*?(?=\n\s*6\.Czy osoba|\n\s*Strona \d+ z \d+)"  # Grupy 11, 12, 13: Funkcja
    r"\s*6\.Czy osoba wchodząca w skład\s+zarządu została zawieszona w\s+czynnościach\?\s+"
    r"(\d*)\s*(\d*|-)\s*(NIE|TAK)\s+"  # Nr wpisu wprow, wykr, Zawieszona (grupy 14, 15, 16)
    r"7\.Data do jakiej została zawieszona\s+-\s+-\s+.*?\s*(?=(\n\s*\d+\s+1\.Nazwisko / Nazwa lub Firma|$))",
    re.DOTALL
)
    for match in person_pattern_nadzor.finditer(relevant_section):
        nazwisko_raw = match.group(4).strip()
        imiona_raw = match.group(7).strip()
        pesel_data_raw = match.group(10).strip().replace(", ------", "").replace("‑‑‑‑‑‑", "").strip()

        person_dict = {
                "Lp": match.group(1).strip(),
                "Nazwisko": ' '.join(nazwisko_raw.split()),
                "Imiona": ' '.join(imiona_raw.split()),
                "PESEL_REGON_DataUrodzenia": pesel_data_raw if pesel_data_raw and pesel_data_raw != '-' else "BRAK DANYCH"
        }
        people_data.append(person_dict)
    return people_data


def extract_prokurenci_info(text_content):
    people_data = []
    start_pattern = re.compile(
            r"Rubryka 3 Prokurenci\s+L\.p\.\s+Numer i nazwa pola\s+Nr wpisu\s+Zawartość\s+wprow\s*\.?\s*wykr\.",
            re.DOTALL)
    end_pattern = re.compile(r"Dział 3", re.DOTALL)

    start_match = start_pattern.search(text_content)
    if not start_match:
        return people_data

    text_after_start = text_content[start_match.end():]
    end_match = end_pattern.search(text_after_start)
    relevant_section = text_after_start[:end_match.start()] if end_match else text_after_start

    # Wzorzec dla prokurentów
    # Pola: Lp, Nazwisko, Imiona, PESEL/DataUrodzenia, RodzajProkury
    person_pattern_prokurenci = re.compile(
            r"(\d+)\s+"  # L.p. (grupa 1)
            r"1\.Nazwisko\s+"
            r"(\d+)\s+(\d+|-)\s+([\S ]+?)\s+"  # Nr wpisu wprow, wykr, Nazwisko (grupy 2,3,4)
            r"2\.Imiona\s+"
            r"(\d+)\s+(\d+|-)\s+([\S ]+?)\s+"  # Nr wpisu wprow, wykr, Imiona (grupy 5,6,7)
            r"3\.Numer PESEL lub data urodzenia\s+"
            r"(\d*)\s*(\d*|-)\s*([\S\s]+?)\s+"  # Nr wpisu wprow, wykr, PESEL/data (grupy 8,9,10)
            r"4\.Rodzaj prokury\s+"
            r"(\d*)\s*(\d*|-)\s*([\S\s]+?)(?=\n\s*\d+\s+1\.Nazwisko|\n\s*Dział 3|\Z)",
            # Nr wpisu wprow, wykr, Rodzaj prokury (grupy 11,12,13)
            re.DOTALL
    )

    for match in person_pattern_prokurenci.finditer(relevant_section):
        nazwisko_raw = match.group(4).strip()
        imiona_raw = match.group(7).strip()
        pesel_data_raw = match.group(10).strip().replace(", ------", "").replace("‑‑‑‑‑‑", "").strip()
        rodzaj_prokury_raw = match.group(13).strip()

        person_dict = {
                "Lp": match.group(1).strip(),
                "Nazwisko": ' '.join(nazwisko_raw.split()),
                "Imiona": ' '.join(imiona_raw.split()),
                "PESEL_REGON_DataUrodzenia": pesel_data_raw if pesel_data_raw and pesel_data_raw != '-' else "BRAK DANYCH",
                "RodzajProkury": ' '.join(rodzaj_prokury_raw.split())
        }
        people_data.append(person_dict)
    return people_data


# Wczytaj zawartość pliku tekstowego
file_path = 'tekst_z_pdf.txt'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    print(f"Błąd: Plik '{file_path}' nie został znaleziony.")
    exit()

# Wyekstrahuj informacje
zarzad_info = extract_zarzad_info(content)
nadzor_info = extract_nadzor_info(content)
prokurenci_info = extract_prokurenci_info(content)

all_extracted_data = {
        "zarzad": zarzad_info,
        "rada_nadzorcza": nadzor_info,
        "prokurenci": prokurenci_info
}

# Zapisz do pliku JSON
output_json_path = 'wszystkie_dane_osob.json'
with open(output_json_path, 'w', encoding='utf-8') as f_json:
    json.dump(all_extracted_data, f_json, indent=4, ensure_ascii=False)

print(f"✅ Dane zostały wyekstrahowane i zapisane do pliku: {output_json_path}")
if not zarzad_info and not nadzor_info and not prokurenci_info:
    print("Nie znaleziono żadnych danych osób w pliku. Sprawdź wzorce regex lub strukturę pliku.")
else:
    print(f"  Znaleziono {len(zarzad_info)} osób w zarządzie.")
    print(f"  Znaleziono {len(nadzor_info)} osób w radzie nadzorczej.")
    print(f"  Znaleziono {len(prokurenci_info)} prokurentów.")
