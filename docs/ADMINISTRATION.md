# Administration und Einstellungen

## Admin-Panel

Das Admin-Panel ist über den **Admin-Button oben rechts** in der Anwendung
erreichbar. Es ist in v1 für die interne Nutzung ohne Authentifizierung
ausgelegt und verwaltet aktuell Stocks.

### Asset-Verwaltung

Die Asset-Tabelle zeigt:

- Asset-Typ
- Name und Ticker-Symbol
- ISIN
- Datenquelle
- letzten erfolgreichen Liefertag
- Datenqualitätsstatus

Über die Aktionen können Assets:

- bearbeitet werden (Stammdaten wie Name, Ticker, ISIN, WKN, Land, Branche
  und Sektor)
- archiviert werden, ohne historische Daten zu löschen
- wieder aktiviert werden
- einzeln neu geladen werden

Archivierte Assets sind standardmäßig ausgeblendet. Mit **Archivierte anzeigen**
können sie eingeblendet und wieder aktiviert werden.

### Datenqualität und Reloads

Ein Asset wird als problematisch angezeigt, wenn kein gespeicherter Tageskurs
für den letzten erwarteten Wochentag vorhanden ist. Wochenenden werden
übersprungen; Börsenfeiertage und individuelle Börsenkalender werden in v1
noch nicht berücksichtigt.

Es gibt drei Reload-Varianten:

- **Reload**: lädt ein einzelnes Asset für den Zeitraum `1mo` mit Tagesintervall
  neu.
- **Reload selected**: lädt die über die Checkboxen ausgewählten aktiven Assets
  neu. Die Auswahl kann über die Checkbox im Tabellenkopf vollständig gesetzt
  oder aufgehoben werden.
- **Reload all**: lädt alle aktiven Assets nacheinander neu.

Nach einem Sammel-Reload werden Anzahl erfolgreicher und fehlgeschlagener
Ladevorgänge angezeigt. Ein Fehlschlag eines einzelnen Assets verhindert nicht,
dass die übrigen Assets verarbeitet werden.

### Asset per Ticker importieren

Über das Importfeld kann ein Ticker-Symbol eingegeben werden. Der Import:

1. ermittelt die Stammdaten über `yfinance`,
2. legt das Asset in der Datenbank an oder aktiviert es wieder,
3. lädt die maximale verfügbare Tageskurs-Historie,
4. lädt verfügbare Fundamentaldaten.

Das Asset wird dabei nicht automatisch einer Watchlist zugeordnet. Die
Watchlist-Zuordnung erfolgt weiterhin über die normale Stock-Verwaltung.

## Einstellungen

Das Einstellungsmenü ist über den **Einstellungen-Button oben rechts**
erreichbar. Einstellungen werden über die Settings-API gespeichert und gelten
global für die Anwendung.

### Ansichtsmodus

Der Ansichtsmodus kann zwischen folgenden Werten umgeschaltet werden:

- **Kompakt**: Standardmodus für die normale Nutzung.
- **Experte**: wird gespeichert; eine vollständig separate Expertenansicht ist
  derzeit noch nicht implementiert.

### Startseite

Die Einstellung **Startseite** legt fest, welche Ansicht nach dem Laden der
Anwendung geöffnet wird. Unterstützte Werte sind:

- Übersicht
- Watchlist
- Screener
- Earnings
- Alerts
- Indizes
- Portfolio
- Investitions-Check

### Theme

Über **Theme** kann zwischen den verfügbaren Farbpaletten gewählt werden.
Die Palette wird als CSS-Variablen auf die Anwendung angewendet. Aktuell
verfügbare Themes sind **Standard** und **Orange**.

### API-Endpunkte

| Bereich | Methode | Endpunkt | Zweck |
|---|---:|---|---|
| Assets | GET | `/admin/assets` | Aktive Assets auflisten |
| Assets | GET | `/admin/assets?include_archived=true` | Inklusive archivierter Assets |
| Assets | PUT | `/admin/assets/{stock_id}` | Stammdaten aktualisieren |
| Assets | DELETE | `/admin/assets/{stock_id}` | Asset archivieren |
| Assets | POST | `/admin/assets/{stock_id}/restore` | Asset aktivieren |
| Reload | POST | `/admin/assets/{stock_id}/reload` | Einzelnes Asset laden |
| Reload | POST | `/admin/assets/reload-selected` | Ausgewählte Assets laden |
| Reload | POST | `/admin/assets/reload-all` | Alle aktiven Assets laden |
| Import | POST | `/admin/assets/import` | Asset per Ticker importieren |
| Settings | GET | `/settings` | Globale Einstellungen lesen |
| Settings | PUT | `/settings` | Globale Einstellungen aktualisieren |
| Themes | GET | `/settings/themes` | Verfügbare Themes lesen |

Die Settings werden in der Tabelle `application_settings` gespeichert.
Archivierte Assets werden über `stocks.is_active` markiert; abhängige Kurs- und
Fundamentaldaten bleiben erhalten.
