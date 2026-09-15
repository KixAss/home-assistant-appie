# Albert Heijn boodschappenlijst voor Home Assistant

Een Home Assistant custom integration die een to-do-lijst-entiteit
toevoegt die twee kanten op synchroniseert met je Albert Heijn
boodschappenlijst: items toevoegen/afvinken in Home Assistant komt in de
AH-app terecht, en andersom. Pure Python, geen externe service of
Docker-container nodig.

> [!NOTE]
> **Dit project is "vibe-coded"**: de code, documentatie en tests in deze
> repo zijn tot stand gekomen in een lopend gesprek met Claude (Anthropic),
> op basis van instructies en feedback van een menselijke gebruiker die
> zelf geen Home Assistant-integraties schrijft. Er is geen persoonlijke
> Python/Home Assistant-expertise aan te pas gekomen om de code
> regel-voor-regel te reviewen. De boel is getest tegen lokale mockservers
> (zie "Wat is getest" verderop) en werkt bij de oorspronkelijke gebruiker,
> maar behandel dit als hobbyproject-kwaliteit, niet als production-grade
> software. Bugs, edge cases en API-aannames die net iets anders liggen
> dan gedacht zijn te verwachten — issues en pull requests zijn welkom.

## Bron & dankbetuiging

Dit project bevat geen gekopieerde code van derden, maar had zonder het
volgende niet kunnen bestaan:

- **[appie-go](https://github.com/gwillem/appie-go)** door
  [@gwillem](https://github.com/gwillem) — een Go-library en CLI voor de
  Albert Heijn mobile API. De endpoints, headers, auth-flow en
  request/response-vormen die hier in Python zijn nagebouwd, zijn afgeleid
  uit het lezen van appie-go's broncode en de meegeleverde
  reverse-engineering-documentatie (`doc/albertheijn_api.md`). appie-go is
  zelf gelicenseerd onder AGPL-3.0; deze repo gebruikt dezelfde licentie
  (zie [LICENSE](LICENSE)) als blijk van respect voor die keuze, ook al is
  dit een onafhankelijke Python-implementatie en geen letterlijke port.

Dit is een niet-officiële, reverse-engineered integratie. Niet
gelieerd aan of onderschreven door Albert Heijn / Ahold Delhaize.
Gebruik op eigen risico.

```
custom_components/appie/
  api.py          Async AH-API-client
  config_flow.py  Config flow: plak de code uit de AH-inlogpagina hier
  coordinator.py  Polling (elke 60s) voor tweerichtings-sync
  todo.py         To-do-lijst-entiteit "Boodschappenlijst"
  __init__.py     Setup + services (add_item, checkout, clear_list)
```

## Hoe dit werkt

`appie-go` is Go; om deze integratie in pure Python te bouwen (zodat er
geen los proces/container nodig is) is `api.py` een eigen implementatie,
geïnformeerd door het lezen van appie-go's broncode en een meegeleverde
documentatiefile met een handmatig samengestelde beschrijving van de AH
mobile API.

Er zitten twee losse, niet-verwante functies in de AH-app die allebei
"lijst" heten:

1. **De klassieke, enkelvoudige boodschappenlijst** — wat de meeste mensen
   bedoelen met "mijn boodschappenlijst". Deze zit in de `shoppinglist/v2`
   endpoints en heeft geen naam of ID nodig: er is er maar één per account.
2. **"Favoriete lijsten" (v3)** — een aparte, nieuwere functie waarmee je
   *meerdere, benoemde* lijstjes kunt hebben (bijv. voor recepten of
   verlanglijstjes). appie-go's Go-wrapper gebruikt uitsluitend déze
   v3-functie.

Deze integratie gebruikt uitsluitend de klassieke v2-lijst (zie
[CHANGELOG.md](CHANGELOG.md) voor hoe dat onderscheid ontdekt werd, na een
paar rondes debuggen met 404's).

Elke functie in `api.py` heeft een `(verified)` of `(inferred)` label:

- **(verified)** — endpoint, headers en JSON-payload komen letterlijk uit
  appie-go's eigen documentatie/code.
- **(inferred)** — voor "item afvinken" en "item verwijderen" bestaat er
  geen apart, gedocumenteerd endpoint in de v2-lijst-API. Beide zijn
  daarom geïmplementeerd door het item opnieuw te versturen via dezelfde
  PATCH die ook voor toevoegen gebruikt wordt: met `strikeThrough` voor
  afvinken, en met `quantity: 0` voor verwijderen (naar analogie van hoe
  AH's Order-API `quantity: 0` gebruikt om een artikel uit je winkelwagen
  te halen). Dit is een onderbouwde aanname, geen bevestigd gedrag van de
  v2-lijst specifiek.

## De login-flow

AH's inlogpagina eindigt altijd met een redirect naar het vaste custom
scheme `appie://login-exit?code=...` (zo onderschept de officiële iOS-app
het) — een gewone browser kan daar niets mee. Deze integratie lost dat
**handmatig** op, in vier stappen die je in de config flow ziet:

1. Open de getoonde inlog-URL in je browser en log in bij Albert Heijn.
2. Na inloggen probeert de pagina te verwijzen naar
   `appie://login-exit?code=...` — je browser kan dat scheme niet openen,
   dat is normaal.
3. Open Chrome DevTools (F12) → tabblad **Network**, vóórdat je de laatste
   inlogstap voltooit. Na het inloggen zie je daar een mislukte aanvraag
   naar `appie://login-exit?code=...`. Klik erop en kopieer de volledige
   URL.
4. Plak die URL (of alleen de code erachter) in het veld in Home
   Assistant.

Home Assistant wisselt die code vervolgens in voor een sessie
(`access_token`/`refresh_token`), die daarna zelf ververst wordt. Verlopen
de codes te snel (ze zijn meestal maar kort geldig), rond de stappen dan
gewoon opnieuw af en plak een nieuwe code.

## Installatie

Kopieer `custom_components/appie` naar de `custom_components`-map van je
Home Assistant, herstart Home Assistant, en voeg de integratie toe via
**Instellingen → Apparaten & Diensten → Integratie toevoegen → "Albert
Heijn boodschappenlijst"**. Volg de vier stappen in het scherm (zie "De
login-flow" hierboven) en plak de code.

Via [HACS](https://hacs.xyz/): voeg deze repo toe als custom repository
(categorie "Integration").

## Wat je krijgt

- Entiteit `todo.boodschappenlijst`, elke 60s gesynchroniseerd:
  - Item toevoegen in HA → toegevoegd als **vrije tekst** aan je AH-lijst
    (standaardgedrag sinds v0.7 — zie [CHANGELOG.md](CHANGELOG.md)).
  - Item afvinken in HA → ook afgevinkt in de AH-app (zie "(inferred)"
    hierboven).
  - Item verwijderen in HA → verwijderd via `quantity: 0` (zie
    "(inferred)" hierboven — niet 100% bevestigd gedrag).
  - Wijzigingen die je rechtstreeks in de AH-app maakt, verschijnen bij de
    volgende refresh ook in HA.
- Services: `appie.add_item` (met optie `free_text: false` voor een
  poging tot echte productkoppeling via zoeken), `appie.checkout` (zet
  product-gekoppelde items om naar bestelling/winkelwagen — vrije-tekst-
  items worden daarbij overgeslagen), `appie.clear_list`.

## Wat is getest

Zonder een echt AH-account kon dit niet end-to-end getest worden. Wel is
`api.py` losstaand gedraaid tegen een lokale mockserver die `api.ah.nl`
nabootst — inclusief een mockserver die de v2-lijst als in-memory state
bijhoudt, zodat toevoegen/afvinken/verwijderen/legen ook echt op elkaar
inwerken zoals bij een live account. Dat dekt: tokens ophalen/verversen
(inclusief het inwisselen van een geplakte code), de v2-lijst ophalen en
parsen, product toevoegen (zoeken én vrije tekst), afvinken/uitvinken met
behoud van aantal, verwijderen, zoeken, omzetten naar bestelling, lijst
legen, en foutafhandeling bij een HTTP 4xx. Het regex-patroon dat de code
uit een geplakte `appie://login-exit?code=...`-URL haalt is los getest met
meerdere varianten. De Python-bestanden zijn syntactisch gecontroleerd; de
volledige Home Assistant-omgeving (met een écht AH-account) kon niet
gedraaid worden tijdens ontwikkeling — dit is dus getest door de
oorspronkelijke gebruiker op een echte installatie, niet door de auteur
van deze code.

## Bekende risico's

- Dit gebruikt een niet-officiële, reverse-engineered API. AH kan endpoints
  of de loginflow op elk moment wijzigen.
- `check_item` (afvinken) en `delete_items` (verwijderen) zijn
  **(inferred)** — zie hierboven.
- De inlogcode van AH is vermoedelijk kortlevend; als het inwisselen
  mislukt met "cannot_connect", rond de loginstappen dan opnieuw af en
  plak een verse code.

Zie [CHANGELOG.md](CHANGELOG.md) voor de volledige geschiedenis van
gevonden bugs en fixes.

## Debug-logging aanzetten

Standaard logt Home Assistant van een custom integration alleen fouten die
expliciet als "error" gelogd worden — niet elke losse API-aanroep. Zet
debug-logging aan om de volledige request/response-uitwisseling met AH te
zien:

- **Via de UI**: Instellingen → Systeem → Logs → rechtsboven "Logboeken
  configureren" → zoek `custom_components.appie` → zet op "Debug".
- **Via `configuration.yaml`**:
  ```yaml
  logger:
    default: warning
    logs:
      custom_components.appie: debug
  ```
  Herstart daarna Home Assistant (of herlaad de logger-configuratie) en
  herlaad de integratie om nieuwe regels te forceren.

Elke regel ziet er dan zo uit:
```
DEBUG (MainThread) [custom_components.appie.api] AH API GET /mobile-services/shoppinglist/v2/items -> HTTP 200: {...}
```

Een item zonder bruikbare naam/productID wordt daarnaast altijd — ook
zónder debug-logging — als **waarschuwing** gelogd met de ruwe AH-data.

## Licentie

[AGPL-3.0](LICENSE), zie "Bron & dankbetuiging" hierboven voor waarom.

## Bijdragen

Issues en pull requests zijn welkom — zeker gezien de "vibe-coded"
herkomst kan een menselijke review op punten die hierboven als
`(inferred)` gemarkeerd staan, geen kwaad.
