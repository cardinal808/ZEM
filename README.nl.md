# ZEM

**ZEM** is een Home Assistant-integratie (HACS) voor thuisaccu's van Zendure. ZEM stuurt één tot drie Zendure-sets lokaal aan via de zenSDK-API, houdt de P1-meter op nul en plant per kwartier laden en leveren op basis van dynamische prijzen en de zonverwachting.

> **Status: in ontwikkeling (0.2, alleen uitlezen).** ZEM leest je Zendure-sets uit en toont hun toestand in Home Assistant. ZEM stuurt de accu **nog niet** aan, dus het kan veilig naast een bestaand systeem draaien.

## Installatie (testversie)
1. In HACS: *Aangepaste repositories* → `https://github.com/cardinal808/ZEM` toevoegen als type *Integratie*, daarna **ZEM** installeren. Of kopieer `custom_components/zem` naar de map `custom_components` van Home Assistant.
2. Herstart Home Assistant.
3. Meestal wordt je set automatisch gevonden (*Instellingen → Apparaten en diensten*). Anders voeg je **ZEM** toe en vul je het IP-adres van de set in.
4. Meer sets (tot 3): open ZEM en kies *Set toevoegen*.

Vereisten: HEMS uit in de Zendure-app; Home Assistant 2026.1 of nieuwer.

## Wat 0.2 biedt
- Per set: laadpercentage, accuvermogen (+ laden, − leveren), laad- en leververmogen, zonnevermogen, status, capaciteit (uit de packs), temperatuur, online en fout.
- Totalen over alle sets: laadpercentage (gewogen naar capaciteit), energie in de accu, capaciteit, vermogen, sets online.
- Diagnose-download met verborgen serienummers en IP-adressen.

[English](README.md)

## Geplande functies
- Modi: Standby, Nul op de meter, Dynamische Forecasting, Snel opladen, Snel ontladen.
- Eén tot drie sets, met de vraag van het huis verdeeld over de sets.
- Planner voor vandaag en morgen (dynamische prijzen, zonverwachting, geleerd verbruik).
- Rendement per set gemeten, zonder invulveld.
- Eigen paneel in de zijbalk van Home Assistant.
- Schaduwmodus: ZEM rekent mee naast een bestaand systeem zonder de accu aan te sturen.

## Herkomst
ZEM is een nieuwe implementatie. Er zit geen code of tekst in van andere Zendure-integraties of -pakketten. Waar andere projecten zijn geraadpleegd, is alleen hun gedrag vergeleken, nadat onze eigen specificatie was geschreven.

## Licentie
MIT, zie [LICENSE](LICENSE).
