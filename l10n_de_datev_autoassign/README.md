# l10n_de_datev_autoassign

Odoo-Modul zur automatischen Vergabe von DATEV-Debitorennummern beim Bestätigen von Ausgangsrechnungen.

## Funktion

Wenn eine Ausgangsrechnung bestätigt wird (`action_post`) und der zugehörige Kunde
noch keine `l10n_de_datev_identifier_customer` besitzt, wird automatisch die nächste
freie Nummer aus der Sequenz `l10n_de_datev_identifier_customer_sequence` vergeben.

## Voraussetzungen

- Odoo 19.0
- Modul `account` (Buchhaltung)
- Modul `l10n_de_reports` (Deutsche Lokalisierung / DATEV-Export)

## Konfiguration

**Einstellungen → Buchhaltung → DATEV Auto-Zuweisung**

| Option | Beschreibung |
|--------|-------------|
| Auto-Zuweisung aktiv | Feature ein-/ausschalten |
| Nächste Nummer | Startwert der Sequenz (Standard: 10000) |

Die Sequenz kann auch direkt unter
**Einstellungen → Technisch → Sequenzen → „DATEV Debitorennummer"** verwaltet werden.

## Sequenz-Konfiguration

| Feld | Standardwert |
|------|-------------|
| Startnummer | 10000 |
| Inkrement | 1 |
| Präfix/Suffix | keiner |
| Mandantenspezifisch | Nein (alle Mandanten teilen eine Sequenz) |

> Für mandantenspezifische Nummernkreise: `company_id` in `data/ir_sequence_data.xml`
> auf den gewünschten Mandanten setzen oder die Sequenz manuell pro Mandant anlegen.

## Hinweise

- Bereits gesetzte Nummern werden **nicht** überschrieben.
- Die Zuweisung erfolgt mit `sudo()`, da Buchhalter i.d.R. keinen Schreibzugriff
  auf `res.partner` haben.
- Die Aktion wird im Server-Log protokolliert (Level: INFO).
