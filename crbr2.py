from zeep import Client, Settings
from zeep.transports import Transport

wsdl_path = "ApiPrzegladoweCRBR.wsdl"
endpoint_url = "https://bramka-crbr.mf.gov.pl:5058/uslugiBiznesowe/uslugiESB/AP/ApiPrzegladoweCRBR/2022/12/01"

settings = Settings(strict=False, xml_huge_tree=True)
transport = Transport(timeout=15)
client = Client(wsdl=wsdl_path, settings=settings, transport=transport)
client.service._binding_options['address'] = endpoint_url

nip = "8992990977"

response = client.service.PobierzInformacjeOSpolkachIBeneficjentach(
    PobierzInformacjeOSpolkachIBeneficjentachDane={
        "SzczegolyWniosku": {"NIP": nip}
    }
)

with open("odpowiedz_crbr.xml", "w", encoding="utf-8") as f:
    f.write(str(response))

print("✅ Odpowiedź zapisana jako odpowiedz_crbr_api_nowe_gpt.xml")
