from zeep import Client
from zeep.transports import Transport
from requests import Session
from requests.auth import HTTPProxyAuth
import urllib3

# Wyłącz ostrzeżenia o niezweryfikowanych certyfikatach SSL (jeśli potrzebne)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Konfiguracja proxy
proxy_config = {
    'http': 'http://twoj_proxy:port',
    'https': 'http://twoj_proxy:port',
}

# Dane uwierzytelniające proxy (jeśli wymagane)
proxy_auth = HTTPProxyAuth('username', 'password')

# Utwórz sesję z proxy
session = Session()
session.proxies = proxy_config
session.auth = proxy_auth
session.verify = False  # Wyłącz weryfikację SSL (jeśli potrzebne)

# Transport z sesją
transport = Transport(session=session)

# Adres WSDL usługi
wsdl_url = 'https://bramka-crbr.mf.gov.pl:5058/uslugiBiznesowe/uslugiESB/AP/ApiPrzegladoweCRBR/2022/12/01?wsdl'

# Utwórz klienta SOAP
client = Client(wsdl_url, transport=transport)

# Przygotuj dane żądania
request_data = {
    'PobierzInformacjeOSpolkachIBeneficjentachDane': {
        'SzczegolyWniosku': {
            'NIP': '1120149662'  # Przykładowy NIP
        }
    }
}

# Wywołaj usługę
try:
    response = client.service.PobierzInformacjeOSpolkachIBeneficjentach(**request_data)
    print("Odpowiedź z API:")
    print(response)
except Exception as e:
    print("Wystąpił błąd podczas wywołania usługi:")
    print(e)
