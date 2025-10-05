-- Migration für Alert-System Phase 1
-- Fügt expiry_date und notes Spalten zur alerts Tabelle hinzu

-- Prüfe ob Spalten bereits existieren
DO $$ 
BEGIN
    -- Füge expiry_date hinzu wenn nicht vorhanden
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'alerts' 
        AND column_name = 'expiry_date'
    ) THEN
        ALTER TABLE alerts ADD COLUMN expiry_date TIMESTAMP NULL;
        RAISE NOTICE 'Spalte expiry_date hinzugefügt';
    ELSE
        RAISE NOTICE 'Spalte expiry_date existiert bereits';
    END IF;

    -- Füge notes hinzu wenn nicht vorhanden
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'alerts' 
        AND column_name = 'notes'
    ) THEN
        ALTER TABLE alerts ADD COLUMN notes TEXT NULL;
        RAISE NOTICE 'Spalte notes hinzugefügt';
    ELSE
        RAISE NOTICE 'Spalte notes existiert bereits';
    END IF;
END $$;

-- Zeige finale Struktur
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'alerts'
ORDER BY ordinal_position;
