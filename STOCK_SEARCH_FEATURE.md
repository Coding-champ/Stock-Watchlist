# 🔍 Stock Search Feature

## Übersicht

Die neue Suchfunktion ermöglicht es Benutzern, Aktien in der Datenbank schnell und einfach zu finden. Die Suche unterstützt mehrere Identifikatoren:

- **Ticker-Symbol** (z.B. AAPL, MSFT)
- **Firmenname** (z.B. Apple, Microsoft)
- **ISIN** (z.B. US0378331005)
- **WKN** (z.B. 865985)

## Features

### 🎯 Intelligente Suche
- **Partial Matching**: Findet Aktien auch bei Teileingaben
- **Case-insensitive**: Groß-/Kleinschreibung spielt keine Rolle
- **Multi-Field Search**: Durchsucht gleichzeitig Name, Ticker, ISIN und WKN

### ⚡ Performance
- **Debouncing**: 300ms Verzögerung für optimierte API-Calls
- **Limit**: Maximal 10 Ergebnisse pro Suche
- **Echtzeit-Feedback**: Loading-Spinner während der Suche

### 🎨 User Experience
- **Tastaturnavigation**: Arrow-Keys, Enter, Escape
- **Hover-States**: Visuelles Feedback bei Mouse-over
- **Highlight**: Suchbegriffe werden in Ergebnissen hervorgehoben
- **Click-outside**: Schließt Dropdown automatisch
- **Responsive**: Mobile-optimiert

### 📊 Ergebnis-Anzeige
Jedes Suchergebnis zeigt:
- Ticker-Symbol (fett)
- Firmenname
- ISIN & WKN (falls vorhanden)
- Sektor
- Aktueller Kurs (falls vorhanden)

## Technische Details

### Backend

**Endpoint**: `GET /stocks/search-db/`

**Query Parameter**:
- `q` (required): Suchbegriff (min. 1 Zeichen)
- `limit` (optional): Max. Anzahl Ergebnisse (default: 20)

**Beispiel**:
```bash
GET /stocks/search-db/?q=apple&limit=10
```

**Response**: Array von Stock-Objekten mit `latest_data`

**SQL Query**:
```sql
SELECT * FROM stocks 
WHERE name ILIKE '%query%' 
   OR ticker_symbol ILIKE '%query%'
   OR isin ILIKE '%query%'
   OR wkn ILIKE '%query%'
LIMIT 20
```

### Frontend

**Komponente**: `StockSearchBar.js`

**Props**:
- `onStockSelect`: Callback-Funktion beim Auswählen einer Aktie
- `placeholder`: Platzhalter-Text (default: "Aktie suchen...")

**State Management**:
- `searchQuery`: Aktueller Suchbegriff
- `searchResults`: Array der Suchergebnisse
- `isSearching`: Loading-Status
- `showResults`: Dropdown-Sichtbarkeit
- `selectedIndex`: Tastaturnavigation

**Hooks**:
- `useEffect`: Debounced API-Calls
- `useEffect`: Click-outside Detection
- `useRef`: DOM-Referenzen (Input, Results, Container)

### Integration in App.js

Die SearchBar wurde in die Top-Navigation integriert:

```jsx
<nav className="topnav">
  <div className="topnav__search">
    <StockSearchBar 
      onStockSelect={(stock) => {
        setSelectedStock(stock);
        setActiveView('stock');
        showToast(`Aktie geöffnet · ${stock.name}`, 'info');
      }}
    />
  </div>
  <div className="topnav__items">
    {/* Navigation Items */}
  </div>
</nav>
```

## UI/UX Design

### Layout
- Position: Ganz links in der Tab-Leiste
- Icon: Lupe (🔍) vor dem Input-Feld
- Breite: Max. 380px (responsive)
- Dropdown: Absolute positioned, max-height 420px

### Styling
- **Primary Color**: `var(--brand-primary)` (#7c3aed)
- **Border Radius**: 12px (Input), 8px (Results)
- **Shadow**: Multi-layer für Tiefe
- **Transitions**: 200ms ease-out
- **Animation**: Fade-in + Slide-down

### States
1. **Default**: Graues Icon, transparenter Background
2. **Focus**: Lila Border, Icon wird lila
3. **Searching**: Spinner rechts
4. **Results**: Dropdown mit Ergebnissen
5. **No Results**: "Keine Aktien gefunden" Message
6. **Selected**: Lila Background, Border

## Tastatur-Shortcuts

| Taste | Aktion |
|-------|--------|
| `↓` | Nächstes Ergebnis |
| `↑` | Vorheriges Ergebnis |
| `Enter` | Ausgewähltes Ergebnis öffnen |
| `Escape` | Dropdown schließen |
| `Tab` | Fokus verlassen |

## Accessibility

- **ARIA Labels**: `aria-label`, `aria-controls`, `aria-expanded`
- **Semantic HTML**: `<nav>`, `<input>`, `<ul>`, `<li>`
- **Keyboard Navigation**: Vollständig tastaturzugänglich
- **Focus Management**: Klare Fokus-States
- **Screen Reader**: Announce-Texte für alle Aktionen

## Performance-Optimierungen

1. **Debouncing**: 300ms Verzögerung
2. **Limit**: Max. 10 Ergebnisse
3. **Index**: DB-Indizes auf allen Suchfeldern
4. **Lazy Loading**: Results nur bei Bedarf
5. **Memo**: React.memo für Result-Items (optional)

## Zukünftige Verbesserungen

- [ ] **Kategorisierung**: Gruppierung nach Sektor/Land
- [ ] **Favoriten**: Zuletzt gesuchte Aktien
- [ ] **Fuzzy Search**: Toleranz für Tippfehler
- [ ] **Autocomplete**: Vorschläge während der Eingabe
- [ ] **Recent Searches**: Historie der letzten Suchen
- [ ] **Advanced Filters**: Filter nach Sektor, Land, etc.
- [ ] **Search Analytics**: Tracking beliebter Suchen

## Testing

### Manuelle Tests
1. Suche nach Ticker: "AAPL"
2. Suche nach Name: "Apple"
3. Suche nach ISIN: "US037833"
4. Suche nach WKN: "865985"
5. Partial Match: "App" → findet "Apple"
6. Case-insensitive: "aapl" = "AAPL"
7. Keine Ergebnisse: "XYZ123"
8. Tastaturnavigation
9. Click-outside
10. Mobile Responsive

### Unit Tests (TODO)
```javascript
describe('StockSearchBar', () => {
  test('renders search input', () => {});
  test('shows loading spinner when searching', () => {});
  test('displays results after search', () => {});
  test('handles no results', () => {});
  test('keyboard navigation works', () => {});
  test('calls onStockSelect when clicking result', () => {});
});
```

## Bekannte Issues

- [ ] Keine
- [ ] Performance bei sehr großen Datenbanken (>10.000 Aktien)
- [ ] Mobile Keyboard überlegt Dropdown (iOS Safari)

## Changelog

### Version 1.0.0 (2025-01-13)
- ✅ Initial Implementation
- ✅ Multi-field Search (Name, Ticker, ISIN, WKN)
- ✅ Keyboard Navigation
- ✅ Responsive Design
- ✅ Highlight Matching Text
- ✅ Integration in TopNav

---

**Erstellt von**: GitHub Copilot  
**Datum**: 13. November 2025  
**Version**: 1.0.0
