import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');

describe('Step 10: Game Map Screen', () => {
  // =========================================================================
  // TerritoryOverlay.tsx
  // =========================================================================
  describe('components/map/TerritoryOverlay.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'components/map/TerritoryOverlay.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(
          path.join(ROOT, 'components/map/TerritoryOverlay.tsx')
        )
      ).toBe(true);
    });

    it('imports Polygon from react-native-maps', () => {
      expect(content).toContain('Polygon');
      expect(content).toContain('react-native-maps');
    });

    it('imports TERRITORY_OVERLAY_COLORS from colors', () => {
      expect(content).toContain('TERRITORY_OVERLAY_COLORS');
    });

    it('imports TerritoryResponse from types/api', () => {
      expect(content).toContain('TerritoryResponse');
    });

    it('uses useMemo for memoization', () => {
      expect(content).toContain('useMemo');
    });

    it('determines ownership color key (own, friend, pvp, cooperative, unclaimed)', () => {
      expect(content).toContain("'own'");
      expect(content).toContain("'friend'");
      expect(content).toContain("'pvp'");
      expect(content).toContain("'cooperative'");
      expect(content).toContain("'unclaimed'");
    });

    it('has tappable prop on Polygon', () => {
      expect(content).toContain('tappable');
    });

    it('has onPress handler for territory tap', () => {
      expect(content).toContain('onPress');
    });

    it('exports TerritoryOverlay component', () => {
      expect(content).toMatch(
        /export\s+(const|function)\s+TerritoryOverlay/
      );
    });
  });

  // =========================================================================
  // EventMarker.tsx
  // =========================================================================
  describe('components/map/EventMarker.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'components/map/EventMarker.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(
          path.join(ROOT, 'components/map/EventMarker.tsx')
        )
      ).toBe(true);
    });

    it('imports Marker from react-native-maps', () => {
      expect(content).toContain('Marker');
      expect(content).toContain('react-native-maps');
    });

    it('imports EventResponse from types/api', () => {
      expect(content).toContain('EventResponse');
    });

    it('has tracksViewChanges={false} for performance', () => {
      expect(content).toContain('tracksViewChanges={false}');
    });

    it('displays countdown timer text', () => {
      expect(content).toMatch(/countdown|time_remaining|formatTime/i);
    });

    it('has tier-specific styling for daily/weekly/monthly', () => {
      expect(content).toContain('daily');
      expect(content).toContain('weekly');
      expect(content).toContain('monthly');
    });

    it('exports EventMarker component', () => {
      expect(content).toMatch(
        /export\s+(const|function)\s+EventMarker/
      );
    });
  });

  // =========================================================================
  // CreatureMarker.tsx
  // =========================================================================
  describe('components/map/CreatureMarker.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'components/map/CreatureMarker.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(
          path.join(ROOT, 'components/map/CreatureMarker.tsx')
        )
      ).toBe(true);
    });

    it('imports Marker from react-native-maps', () => {
      expect(content).toContain('Marker');
      expect(content).toContain('react-native-maps');
    });

    it('has tracksViewChanges={false} for performance', () => {
      expect(content).toContain('tracksViewChanges={false}');
    });

    it('displays creature icon', () => {
      expect(content).toMatch(/creature|icon|MaterialIcons/);
    });

    it('exports CreatureMarker component', () => {
      expect(content).toMatch(
        /export\s+(const|function)\s+CreatureMarker/
      );
    });
  });

  // =========================================================================
  // LootIndicator.tsx
  // =========================================================================
  describe('components/map/LootIndicator.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'components/map/LootIndicator.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(
          path.join(ROOT, 'components/map/LootIndicator.tsx')
        )
      ).toBe(true);
    });

    it('does NOT import from react-native-reanimated (uses RN Animated instead)', () => {
      expect(content).not.toContain('react-native-reanimated');
    });

    it('imports Marker from react-native-maps', () => {
      expect(content).toContain('Marker');
      expect(content).toContain('react-native-maps');
    });

    it('uses tracksViewChanges prop on Marker', () => {
      expect(content).toContain('tracksViewChanges={tracksViewChanges}');
    });

    it('uses Animated.loop for pulsing animation', () => {
      expect(content).toContain('Animated.loop');
    });

    it('exports LootIndicator component', () => {
      expect(content).toMatch(
        /export\s+(const|function)\s+LootIndicator/
      );
    });
  });

  // =========================================================================
  // TerritoryInfoSheet.tsx
  // =========================================================================
  describe('components/map/TerritoryInfoSheet.tsx', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'components/map/TerritoryInfoSheet.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(
          path.join(ROOT, 'components/map/TerritoryInfoSheet.tsx')
        )
      ).toBe(true);
    });

    it('imports BottomSheet from @gorhom/bottom-sheet', () => {
      expect(content).toContain('@gorhom/bottom-sheet');
      expect(content).toContain('BottomSheet');
    });

    it('imports TerritoryResponse from types/api', () => {
      expect(content).toContain('TerritoryResponse');
    });

    it('displays zone type', () => {
      expect(content).toContain('zone_type');
    });

    it('displays owner information', () => {
      expect(content).toContain('owner_username');
    });

    it('displays chief creature', () => {
      expect(content).toContain('chief_creature_id');
    });

    it('displays passive reward rate', () => {
      expect(content).toContain('passive_reward_rate');
    });

    it('displays familiarity score', () => {
      expect(content).toMatch(/familiar_score_for_user|familiarity/i);
    });

    it('exports TerritoryInfoSheet component', () => {
      expect(content).toMatch(
        /export\s+(const|function)\s+TerritoryInfoSheet/
      );
    });

    it('uses ZONE_COLORS for zone type display', () => {
      expect(content).toContain('ZONE_COLORS');
    });
  });

  // =========================================================================
  // Game Map Screen - app/(tabs)/index.tsx
  // =========================================================================
  describe('app/(tabs)/index.tsx (Game Map Screen)', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'app/(tabs)/index.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(path.join(ROOT, 'app/(tabs)/index.tsx'))
      ).toBe(true);
    });

    it('imports MapView from react-native-maps', () => {
      expect(content).toContain('react-native-maps');
    });

    it('uses useNearbyTerritories hook', () => {
      expect(content).toContain('useNearbyTerritories');
    });

    it('uses useNearbyEvents hook', () => {
      expect(content).toContain('useNearbyEvents');
    });

    it('uses useLocationTracking hook', () => {
      expect(content).toContain('useLocationTracking');
    });

    it('uses useLocationStore for GPS coordinates', () => {
      expect(content).toContain('useLocationStore');
    });

    it('uses useMapStore for map region', () => {
      expect(content).toContain('useMapStore');
    });

    it('renders TerritoryOverlay component', () => {
      expect(content).toContain('TerritoryOverlay');
    });

    it('renders EventMarker component', () => {
      expect(content).toContain('EventMarker');
    });

    it('renders CreatureMarker component', () => {
      expect(content).toContain('CreatureMarker');
    });

    it('renders LootIndicator component', () => {
      expect(content).toContain('LootIndicator');
    });

    it('renders TerritoryInfoSheet component', () => {
      expect(content).toContain('TerritoryInfoSheet');
    });

    it('uses useMemo for viewport-based territory filtering', () => {
      expect(content).toContain('useMemo');
    });

    it('uses useCallback for event handlers', () => {
      expect(content).toContain('useCallback');
    });

    it('handles onRegionChangeComplete for map region updates', () => {
      expect(content).toContain('onRegionChangeComplete');
    });

    it('shows location permission denied banner', () => {
      expect(content).toContain('permissionGranted');
      expect(content).toContain('permissionChecked');
    });

    it('uses GAME_COLORS from colors constants', () => {
      expect(content).toContain('GAME_COLORS');
    });

    it('uses LoadingSpinner component', () => {
      expect(content).toContain('LoadingSpinner');
    });

    it('has default location fallback for map center', () => {
      expect(content).toContain('DEFAULT_LOCATION');
    });

    it('exports default MapScreen function', () => {
      expect(content).toMatch(/export\s+default\s+function\s+MapScreen/);
    });
  });

  // =========================================================================
  // Extended TerritoryResponse type
  // =========================================================================
  describe('types/api.ts (territory boundary extension)', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'types/api.ts'),
        'utf-8'
      );
    });

    it('TerritoryResponse includes boundary_coordinates for polygon rendering', () => {
      expect(content).toContain('boundary_coordinates');
    });

    it('TerritoryResponse includes center_lat and center_lon for marker positioning', () => {
      expect(content).toContain('center_lat');
      expect(content).toContain('center_lon');
    });

    it('TerritoryResponse includes area_name for display', () => {
      expect(content).toContain('area_name');
    });

    it('TerritoryResponse includes chief_creature_name for display', () => {
      expect(content).toContain('chief_creature_name');
    });

    it('TerritoryResponse includes is_friend flag for overlay coloring', () => {
      expect(content).toContain('is_friend');
    });
  });
});
