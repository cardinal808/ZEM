# ZEM

**ZEM** is een Home Assistant-integratie (HACS) voor thuisaccu's van Zendure. ZEM stuurt één tot drie Zendure-sets lokaal aan via de zenSDK-API, houdt de P1-meter op nul en plant per kwartier laden en leveren op basis van dynamische prijzen en de zonverwachting.

> **Status: in ontwikkeling.** Nog niet bruikbaar. De eerste mijlpaal (M1) bevat de kern die de lokale API van de accu uitleest en interpreteert, met tests.

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
