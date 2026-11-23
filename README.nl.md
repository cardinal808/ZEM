# ZEPHYR

*Zendure Energy Planning, Home Yield & Regulation*  
**Forecasting Tomorrow. Planning Today.**

**ZEPHYR** is een Home Assistant-integratie (HACS) voor thuisaccu's van Zendure. ZEPHYR stuurt één tot drie Zendure-sets lokaal aan via de zenSDK-API, houdt de P1-meter op nul en plant per kwartier laden en leveren op basis van dynamische prijzen en de zonverwachting.

> **Status: in ontwikkeling (0.4, schaduwmodus).** ZEPHYR leest je Zendure-sets uit en rekent elke seconde uit wat het zou doen om je meter op nul te houden, maar stuurt de accu **nog niet** aan. Het kan veilig naast een bestaand systeem draaien, zodat je kunt vergelijken.

> **Overstappen van ZEM (0.3.x)?** De integratie heeft een nieuwe naam en het domein is veranderd van `zem` naar `zephyr`. Verwijder in HACS de integratie ZEM en de oude custom repository, voeg `https://github.com/cardinal808/ZEPHYR` toe, installeer ZEPHYR, herstart Home Assistant en voeg ZEPHYR opnieuw toe. De entiteiten heten nu `sensor.zephyr_…`.

## Installatie (testversie)
1. In HACS: *Aangepaste repositories* → `https://github.com/cardinal808/ZEPHYR` toevoegen als type *Integratie*, daarna **ZEPHYR** installeren. Of kopieer `custom_components/zephyr` naar de map `custom_components` van Home Assistant.
2. Herstart Home Assistant.
3. Meestal wordt je set automatisch gevonden (*Instellingen → Apparaten en diensten*). Anders voeg je **ZEPHYR** toe en vul je het IP-adres van de set in.
4. Meer sets (tot 3): open ZEPHYR en kies *Set toevoegen*.
5. Open ZEPHYR → *Configureren* en kies je P1-meter (wordt automatisch voorgesteld): één netto sensor, of de sensoren voor afname en teruglevering van de DSMR-integratie (aanbevolen: die melden elk telegram). De schaduwmodus start in de modus *Nul op de meter*.

Vereisten: HEMS uit in de Zendure-app; Home Assistant 2026.1 of nieuwer.

## Wat 0.3 biedt
- Schaduwmodus: `sensor.zephyr_setpoint` (wat ZEPHYR van de accu zou vragen, + laden, − leveren), `sensor.zephyr_action`, `sensor.zephyr_reason` (in gewone taal), `select.zephyr_mode`, `binary_sensor.zephyr_p1_ok`, en per set `sensor.zephyr_set_1_setpoint`. Er wordt niets naar de accu gestuurd.
- Het beslislog staat in de diagnose-download.
- Per set: laadpercentage, accuvermogen (+ laden, − leveren), laad- en leververmogen, zonnevermogen, status, capaciteit (uit de packs), temperatuur, online en fout.
- Totalen over alle sets: laadpercentage (gewogen naar capaciteit), energie in de accu, capaciteit, vermogen, sets online.
- Diagnose-download met verborgen serienummers en IP-adressen.

[English](README.md)

## Ondersteunde sets en accu's
- Sets met de lokale zenSDK-API: SolarFlow 800, 800 Plus, 800 Pro, 1600 AC+, 2400 AC, 2400 AC+, 2400 Pro en 4000 AC+. Tot nu toe getest: 2400 Pro en 2400 AC+. Zet HEMS uit in de Zendure-app.
- Accu's worden herkend aan hun serienummer: AB1000, AB1000S, AB2000(S/X), AB3000X, AB3000L en de ingebouwde accu's van de 2400 Pro, 2400 AC+, 4000 AC+ en AIO 2400.
- Nieuwere modellen (800 AC+, 800 Pro 2, 3000/4000 Mix) en accu's (AB2000L, AB3000S, B6400) werken waarschijnlijk voor uitlezen, maar staan nog niet in de tabellen; met een diagnose-download kunnen we ze toevoegen.
- **Niet ondersteund** (geen lokale zenSDK-API): SolarFlow Hub 1200/2000, Hyper 2000, Ace 1500, AIO 2400 en SuperBase. Alleen de ingebouwde accu van een AIO 2400 die als extra pack aan een SolarFlow hangt, wordt herkend.
- Accu niet herkend? Home Assistant toont een reparatiemelding. Vul de capaciteit in via ZEPHYR → de set → *Opnieuw configureren*, en open graag een issue met de regel uit de melding, dan voegen we hem toe.

## Geplande functies
- Modi: Standby, Nul op de meter, Dynamische Forecasting, Snel opladen, Snel ontladen.
- Eén tot drie sets, met de vraag van het huis verdeeld over de sets.
- Planner voor vandaag en morgen (dynamische prijzen, zonverwachting, geleerd verbruik).
- Rendement per set gemeten, zonder invulveld.
- Eigen paneel in de zijbalk van Home Assistant.
- Schaduwmodus: ZEPHYR rekent mee naast een bestaand systeem zonder de accu aan te sturen.

## Herkomst
ZEPHYR is een nieuwe implementatie. Er zit geen code of tekst in van andere Zendure-integraties of -pakketten. Waar andere projecten zijn geraadpleegd, is alleen hun gedrag vergeleken, nadat onze eigen specificatie was geschreven.

## Licentie
MIT, zie [LICENSE](LICENSE).
