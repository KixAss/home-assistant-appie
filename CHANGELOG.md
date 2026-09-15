# Changelog

- **v0.7** — Items worden nu **standaard als vrije tekst** toegevoegd, in
  zowel de to-do-lijst als de `appie.add_item`-service. Dat is
  betrouwbaarder dan productmatching via zoeken: vrije tekst gebruikt
  exact de veldstructuur uit de documentatie die al bevestigd klopt (geen
  zoek-mismatches zoals "Bolletje" → "Bolognese chips", geen onbekende
  velden zoals bij "Product #0"). Wil je alsnog een echte productkoppeling
  (bijv. nodig voor `appie.checkout`), zet dan `free_text: false` in de
  service-aanroep — de verbeterde zoek-matching uit v0.6 blijft
  beschikbaar voor wie dat wil.
- **v0.6** — Twee fixes:
  - **Verkeerd product gematcht bij toevoegen** (bijv. "Bolletje" werd
    "Bolognese chips"). Bleek te komen doordat we AH's zoek-endpoint met
    `size=1` aanriepen — met maar één gevraagd resultaat is AH's
    "relevantste" resultaat kennelijk niet betrouwbaar. We vragen nu 10
    resultaten op en kiezen zelf de beste match (exacte titel-match, dan
    titel die met de zoekterm begint, dan titel die alle zoekwoorden
    bevat). Vindt niets redelijks, dan valt het terug op vrije tekst in
    plaats van een gok te wagen.
  - **"Product #0" in Home Assistant**: een item met zowel een lege naam
    als `product_id: 0` geeft aan dat AH's antwoord voor dat specifieke
    item geen bruikbare `description`/`productId` bevatte. Dit wordt nu
    ook zichtbaar gelogd als **waarschuwing** (dus zonder dat je
    debug-logging hoeft aan te zetten) met de volledige ruwe data van dat
    item.
- **v0.5** — Grote fix: de integratie gebruikte per ongeluk de "favoriete
  lijsten" (v3)-functie (meerdere, benoemde lijstjes) in plaats van de
  klassieke, enkelvoudige boodschappenlijst (v2) — die twee zijn losse
  functies in de AH-app. `api.py` is herschreven om uitsluitend
  `/mobile-services/shoppinglist/v2/items` te gebruiken (hetzelfde
  endpoint dat toevoegen al die tijd al gebruikte, en dat wél werkte). Dit
  loste de aanhoudende `HTTP 404` op. Afvinken en verwijderen zijn nu
  geïmplementeerd via een PATCH-hergebruik-truc i.p.v. de niet-werkende
  v3 GraphQL-mutatie. Alles is end-to-end getest tegen een mockserver die
  de lijst als levende state bijhoudt.
- **v0.4** — Een `HTTP 404` op het lijst-endpoint wordt nu opgevangen als
  "nog geen boodschappenlijst aangemaakt" (i.p.v. als harde fout). Verder
  wordt élke AH-API-aanroep nu op debug-niveau gelogd (methode, pad,
  status, response-body).
- **v0.3** — `productId` in `/mobile-services/lists/v3/lists` kwam van een
  live zoekopdracht ("melk") in plaats van een hardcoded `1` (later in
  v0.5 bleek dit hele endpoint niet de juiste aanpak; zie boven).
- **v0.2** — Login werd handmatig (plak de `appie://login-exit?code=...`
  URL uit Chrome DevTools) in plaats van via een lokale
  reverse-proxy-server, die in de praktijk niet betrouwbaar bleek.
- **v0.1** — Eerste pure-Python versie, zonder losse Go-`appie-bridge`.
