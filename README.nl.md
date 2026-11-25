<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/logo-dark.png">
    <img src="docs/logo.png" alt="ZEPHYR" width="280">
  </picture>
</p>

# ZEPHYR

*Zendure Energy Planning, Home Yield & Regulation*  
**Forecasting Tomorrow. Planning Today.**

**ZEPHYR** is een Home Assistant-integratie (HACS) voor thuisaccu's van Zendure. ZEPHYR stuurt één tot drie Zendure-sets lokaal aan via de zenSDK-API, houdt de P1-meter op nul en plant per kwartier laden en leveren op basis van dynamische prijzen en de zonverwachting.

> **Status: in ontwikkeling (0.5, testfase live sturen).** Standaard draait ZEPHYR in de schaduwmodus: het leest je Zendure-sets uit en rekent elke seconde uit wat het zou doen, zonder de accu aan te sturen, zodat je veilig kunt vergelijken met je huidige systeem. Met de schakelaar **"ZEPHYR stuurt de accu"** (`switch.zephyr_control`) stuurt ZEPHYR de accu echt aan in de modus Nul op de meter. Zet dan eerst je huidige aansturing uit.

> **Overstappen van ZEM (0.3.x)?** De integratie heeft een nieuwe naam en het domein is veranderd van `zem` naar `zephyr`. Verwijder in HACS de integratie ZEM en de oude custom repository, voeg `https://github.com/cardinal808/ZEPHYR` toe, installeer ZEPHYR, herstart Home Assistant en voeg ZEPHYR opnieuw toe. De entiteiten heten nu `sensor.zephyr_…`.

## Installatie (testversie)
1. In HACS: *Aangepaste repositories* → `https://github.com/cardinal808/ZEPHYR` toevoegen als type *Integratie*, daarna **ZEPHYR** installeren. Of kopieer `custom_components/zephyr` naar de map `custom_components` van Home Assistant.
2. Herstart Home Assistant.
3. Meestal wordt je set automatisch gevonden (*Instellingen → Apparaten en diensten*). Anders voeg je **ZEPHYR** toe en vul je het IP-adres van de set in.
4. Meer sets (tot 3): open ZEPHYR en kies *Set toevoegen*.
5. Open ZEPHYR → *Configureren* en kies je P1-meter (wordt automatisch voorgesteld): één netto sensor, of de sensoren voor afname en teruglevering van de DSMR-integratie (aanbevolen: die melden elk telegram). De schaduwmodus start in de modus *Nul op de meter*.

Vereisten: HEMS uit in de Zendure-app; Home Assistant 2026.1 of nieuwer.

## Wat 0.3 biedt
- Schaduwmodus: `sensor.zephyr_setpoint` (wat ZEPHYR van de accu zou vragen, + laden, − leveren), `sensor.zephyr_action`, `sensor.zephyr_reason` (in gewone taal), `select.zephyr_mode`, `binary_sensor.zephyr_p1_ok`, en per set `sensor.zephyr_set_1_setpoint`. Er wordt niets naar de accu gestuurd. ZEPHYR rekent met een virtuele set die zijn eigen commando's uitvoert, in plaats van de echte set die je huidige systeem aanstuurt; de diagnostiek vergelijkt afname en teruglevering van beide (`control.twin`).
- Het beslislog staat in de diagnose-download.
- Per set: laadpercentage, accuvermogen (+ laden, − leveren), laad- en leververmogen, zonnevermogen, status, capaciteit (uit de packs), temperatuur, online en fout.
- Totalen over alle sets: laadpercentage (gewogen naar capaciteit), energie in de accu, capaciteit, vermogen, sets online.
- Diagnose-download met verborgen serienummers en IP-adressen.

[English](README.md)

## Live sturen (0.5, testfase)
- **Schakelaar** `switch.zephyr_control`, standaard uit. Aanzetten lukt alleen als de P1 meldt en de set online is zonder fout; ZEPHYR gaat verder vanaf wat de set nu doet (geen dip). Uitzetten: één keer 0 W, daarna neemt je huidige systeem het weer over. Na een herstart blijft de schakelaar uit (optie *Live sturen uit na herstart*, standaard aan tijdens de testfase).
- **Alleen leveren in de duurste uren** (optioneel): kies in de opties een Nord Pool-prijssensor. ZEPHYR levert dan alleen in de N duurste uren van de dag (standaard 4) en laadt verder alleen met zon. **Reserve** (standaard 20 %): zit de accu eronder, dan laadt ZEPHYR bij in de goedkoopste uren vóór het volgende dure blok; in de dure uren mag de reserve gewoon gebruikt worden.
- **Veiligheid:** stuurt een ander systeem de set, dan stopt ZEPHYR met schrijven en meldt dat. Te veel schrijfacties naar flash: standby wordt 0 W in RAM. HA stopt: eerst alle sets 0 W.
- **Schrijftest:** actie `zephyr.test_command` (bijvoorbeeld `power: -300` = 60 s 300 W leveren, daarna standby), alleen in de schaduwmodus met de modus Standby.
- **Testdashboard:** [`dashboards/zephyr-test.yaml`](dashboards/zephyr-test.yaml) met de schakelaar, de modus, knoppen voor de schrijftest, een grafiek en de tellers. Toevoegen: *Instellingen → Dashboards → Dashboard toevoegen*, openen, ⋮ → *Dashboard bewerken* → ⋮ → *Ruwe configuratie-editor*, en het bestand plakken. Tellers niet zichtbaar? Schakel `sensor.zephyr_set_1_write_count` en `…_switch_count` in (bij installaties van vóór 0.5.2 staan ze standaard uit).

## Kostenlogboek (0.6)
- Per kwartier: afname, teruglevering, accu geladen/geleverd, zon en de Nord Pool-prijs, met de kosten **werkelijk**, **zonder accu** en **zonder accu en zon**. Werkt ook in de schaduwmodus (dan: de kosten van je huidige systeem).
- Vul in de opties je **eigen tarieven** in: energiebelasting (2026: €0,0916), opslag inkoop en teruglevering, btw en eventueel de vaste kosten per maand. Een lijst met leveranciers volgt. Saldering (t/m 2026) wordt meegerekend en per jaar verrekend.
- Optioneel de kWh-tellers van je meter (tarief 1 en 2) voor afname en teruglevering; zonder tellers integreert ZEPHYR het P1-vermogen. Met een zonteller ook de besparing door de zon.
- Entiteiten: `sensor.zephyr_costs_today|month|year` en `sensor.zephyr_savings_today|month|year` (€), met de uitsplitsing als attributen. Actie `zephyr.export_costs` schrijft de kwartieren als CSV naar `config/zephyr/`.

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
