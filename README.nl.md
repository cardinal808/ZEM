# ZEM

**ZEM** is een Home Assistant-integratie (HACS) voor thuisaccu's van Zendure. ZEM stuurt één tot drie Zendure-sets lokaal aan via de zenSDK-API, houdt de P1-meter op nul en plant per kwartier laden en leveren op basis van dynamische prijzen en de zonverwachting.

> **Status: in ontwikkeling (0.3, schaduwmodus).** ZEM leest je Zendure-sets uit en rekent elke seconde uit wat het zou doen om je meter op nul te houden, maar stuurt de accu **nog niet** aan. Het kan veilig naast een bestaand systeem draaien, zodat je kunt vergelijken.

## Installatie (testversie)
1. In HACS: *Aangepaste repositories* → `https://github.com/cardinal808/ZEM` toevoegen als type *Integratie*, daarna **ZEM** installeren. Of kopieer `custom_components/zem` naar de map `custom_components` van Home Assistant.
2. Herstart Home Assistant.
3. Meestal wordt je set automatisch gevonden (*Instellingen → Apparaten en diensten*). Anders voeg je **ZEM** toe en vul je het IP-adres van de set in.
4. Meer sets (tot 3): open ZEM en kies *Set toevoegen*.
5. Open ZEM → *Configureren* en kies je P1-meter (wordt automatisch voorgesteld). De schaduwmodus start in de modus *Nul op de meter*.

Vereisten: HEMS uit in de Zendure-app; Home Assistant 2026.1 of nieuwer.

## Wat 0.3 biedt
- Schaduwmodus: `sensor.zem_setpoint` (wat ZEM van de accu zou vragen, + laden, − leveren), `sensor.zem_action`, `sensor.zem_reason` (in gewone taal), `select.zem_mode`, `binary_sensor.zem_p1_ok`, en per set `sensor.zem_set_1_setpoint`. Er wordt niets naar de accu gestuurd.
- Het beslislog staat in de diagnose-download.
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
