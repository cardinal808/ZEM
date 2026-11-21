# ZEM

**ZEM** is a Home Assistant integration (HACS) for Zendure home batteries. It controls one to three Zendure sets locally through the zenSDK API, keeps the grid meter at zero, and plans charging and discharging per quarter hour from dynamic prices and solar forecasts.

> **Status: in development.** Not usable yet. The first milestone (M1) contains the core that reads and interprets the battery's local API, with tests.

[Nederlands](README.nl.md)

## Planned features
- Modes: Standby, Zero meter, Dynamic Forecasting, Fast charge, Fast discharge.
- One to three sets, with the grid demand distributed over the sets.
- Planner for today and tomorrow (dynamic prices, solar forecast, learned consumption).
- Efficiency measured per set, no manual input.
- Own panel in the Home Assistant sidebar.
- Shadow mode: ZEM calculates alongside an existing setup without controlling the battery.

## Origin
ZEM is a new implementation. It contains no code or text from other Zendure integrations or packages. Where other projects were consulted, only their behaviour was compared, after our own specification was written.

## License
MIT, see [LICENSE](LICENSE).
