import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');

describe('Step 9: Map Screen with Pins, Filters, and Bottom Sheet', () => {
  // =========================================================================
  // 1. Tab Layout
  // =========================================================================
  describe('app/(tabs)/_layout.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(tabs)/_layout.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports MaterialIcons', () => {
      expect(content).toContain('MaterialIcons');
    });

    it('uses Tabs from expo-router', () => {
      expect(content).toContain('Tabs');
      expect(content).toContain('expo-router');
    });

    it('has Map tab with map icon (index)', () => {
      expect(content).toContain('"index"');
      expect(content).toContain('"map"');
      expect(content).toContain('Map');
    });

    it('has Explore tab with explore icon', () => {
      expect(content).toContain('"explore"');
      expect(content).toMatch(/name=["']explore["']/);
    });

    it('has Journal tab with book icon', () => {
      expect(content).toContain('"journal"');
      expect(content).toMatch(/name=["']book["']/);
    });

    it('has Profile tab with person icon', () => {
      expect(content).toContain('"profile"');
      expect(content).toMatch(/name=["']person["']/);
    });

    it('has exactly 4 Tabs.Screen components', () => {
      const matches = content.match(/Tabs\.Screen/g);
      expect(matches).not.toBeNull();
      expect(matches!.length).toBe(4);
    });

    it('active tab has visual highlighting via tabBarActiveTintColor', () => {
      expect(content).toContain('tabBarActiveTintColor');
    });

    it('exports a default layout function', () => {
      expect(content).toMatch(/export\s+default\s+function/);
    });
  });

  // =========================================================================
  // 2. placesService.ts
  // =========================================================================
  describe('services/placesService.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'services/placesService.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports api instance from ./api', () => {
      expect(content).toContain("from './api'");
    });

    it('imports PlaceResponse type', () => {
      expect(content).toContain('PlaceResponse');
    });

    it('imports PlaceDetailResponse type', () => {
      expect(content).toContain('PlaceDetailResponse');
    });

    it('imports ForecastResponse type', () => {
      expect(content).toContain('ForecastResponse');
    });

    it('exports getNearbyPlaces function', () => {
      expect(content).toMatch(
        /export\s+(const|async\s+function|function)\s+getNearbyPlaces/
      );
    });

    it('getNearbyPlaces accepts lat, lon, radius, and optional category', () => {
      expect(content).toMatch(/getNearbyPlaces[\s\S]*lat/);
      expect(content).toMatch(/getNearbyPlaces[\s\S]*lon/);
      expect(content).toMatch(/getNearbyPlaces[\s\S]*radius/);
    });

    it('getNearbyPlaces calls GET /places/nearby', () => {
      expect(content).toContain('/places/nearby');
    });

    it('exports getPlaceDetail function', () => {
      expect(content).toMatch(
        /export\s+(const|async\s+function|function)\s+getPlaceDetail/
      );
    });

    it('getPlaceDetail calls GET /places/ with id', () => {
      expect(content).toMatch(/\/places\/.*id/);
    });

    it('exports getForecast function', () => {
      expect(content).toMatch(
        /export\s+(const|async\s+function|function)\s+getForecast/
      );
    });

    it('getForecast calls GET /places/{id}/forecast with day and hour params', () => {
      expect(content).toContain('/forecast');
      expect(content).toContain('day');
      expect(content).toContain('hour');
    });
  });

  // =========================================================================
  // 3. visitsService.ts
  // =========================================================================
  describe('services/visitsService.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'services/visitsService.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports api instance from ./api', () => {
      expect(content).toContain("from './api'");
    });

    it('imports GPSPingResponse type', () => {
      expect(content).toContain('GPSPingResponse');
    });

    it('imports VisitResponse type', () => {
      expect(content).toContain('VisitResponse');
    });

    it('exports postGpsPing function', () => {
      expect(content).toMatch(
        /export\s+(const|async\s+function|function)\s+postGpsPing/
      );
    });

    it('postGpsPing accepts lat, lon, accuracy, and timestamp', () => {
      expect(content).toMatch(/postGpsPing[\s\S]*lat/);
      expect(content).toMatch(/postGpsPing[\s\S]*lon/);
      expect(content).toMatch(/postGpsPing[\s\S]*accuracy/);
      expect(content).toMatch(/postGpsPing[\s\S]*timestamp/);
    });

    it('postGpsPing calls POST /visits/ping', () => {
      expect(content).toContain('/visits/ping');
      expect(content).toContain('.post');
    });

    it('exports getVisitHistory function', () => {
      expect(content).toMatch(
        /export\s+(const|async\s+function|function)\s+getVisitHistory/
      );
    });

    it('getVisitHistory calls GET /visits/history with limit and offset', () => {
      expect(content).toContain('/visits/history');
      expect(content).toContain('limit');
      expect(content).toContain('offset');
    });
  });

  // =========================================================================
  // 4. locationService.ts
  // =========================================================================
  describe('services/locationService.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'services/locationService.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports expo-location', () => {
      expect(content).toContain('expo-location');
    });

    it('exports startTracking function', () => {
      expect(content).toMatch(
        /export\s+(const|async\s+function|function)\s+startTracking/
      );
    });

    it('uses watchPositionAsync for location tracking', () => {
      expect(content).toContain('watchPositionAsync');
    });

    it('uses distanceInterval for 15s tracking', () => {
      expect(content).toContain('distanceInterval');
    });

    it('exports stopTracking function', () => {
      expect(content).toMatch(
        /export\s+(const|async\s+function|function)\s+stopTracking/
      );
    });

    it('removes location subscription on stop', () => {
      expect(content).toContain('remove');
    });
  });

  // =========================================================================
  // 5. useNearbyPlaces hook
  // =========================================================================
  describe('hooks/useNearbyPlaces.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'hooks/useNearbyPlaces.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports useQuery from @tanstack/react-query', () => {
      expect(content).toContain('useQuery');
      expect(content).toContain('@tanstack/react-query');
    });

    it('imports getNearbyPlaces from placesService', () => {
      expect(content).toContain('getNearbyPlaces');
      expect(content).toContain('placesService');
    });

    it('exports useNearbyPlaces hook', () => {
      expect(content).toMatch(
        /export\s+(const|function)\s+useNearbyPlaces/
      );
    });

    it('uses queryKey with places, nearby, lat, lon, radius, category', () => {
      expect(content).toContain("'places'");
      expect(content).toContain("'nearby'");
      expect(content).toContain('lat');
      expect(content).toContain('lon');
      expect(content).toContain('radius');
      expect(content).toContain('category');
    });

    it('sets staleTime to 5 minutes (STALE_TIME.PLACES or 300000)', () => {
      expect(content).toMatch(/STALE_TIME\.PLACES|300000|5\s*\*\s*60\s*\*\s*1000/);
    });
  });

  // =========================================================================
  // 6. useLocationTracking hook
  // =========================================================================
  describe('hooks/useLocationTracking.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'hooks/useLocationTracking.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports expo-location', () => {
      expect(content).toContain('expo-location');
    });

    it('imports useLocationStore', () => {
      expect(content).toContain('useLocationStore');
    });

    it('exports useLocationTracking hook', () => {
      expect(content).toMatch(
        /export\s+(const|function)\s+useLocationTracking/
      );
    });

    it('requests foreground location permission', () => {
      expect(content).toContain('requestForegroundPermissionsAsync');
    });

    it('uses watchPositionAsync for GPS tracking', () => {
      expect(content).toContain('watchPositionAsync');
    });

    it('updates locationStore with setLocation', () => {
      expect(content).toContain('setLocation');
    });

    it('returns permission status', () => {
      expect(content).toMatch(/permission|Permission/);
    });
  });

  // =========================================================================
  // 7. PlacePin component
  // =========================================================================
  describe('components/map/PlacePin.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'components/map/PlacePin.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports Marker from react-native-maps', () => {
      expect(content).toContain('react-native-maps');
      expect(content).toContain('Marker');
    });

    it('uses green color #22c55e for quiet (0-33)', () => {
      expect(content).toContain('#22c55e');
    });

    it('uses yellow color #eab308 for moderate (34-66)', () => {
      expect(content).toContain('#eab308');
    });

    it('uses red color #ef4444 for busy (67-100)', () => {
      expect(content).toContain('#ef4444');
    });

    it('uses grey color #9ca3af for no data', () => {
      expect(content).toContain('#9ca3af');
    });

    it('sets tracksViewChanges to false for performance', () => {
      expect(content).toContain('tracksViewChanges');
      expect(content).toMatch(/tracksViewChanges=\{false\}/);
    });

    it('exports PlacePin component', () => {
      expect(content).toMatch(
        /export\s+(const|function|default\s+function)\s+PlacePin/
      );
    });
  });

  // =========================================================================
  // 8. CategoryFilter component
  // =========================================================================
  describe('components/map/CategoryFilter.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'components/map/CategoryFilter.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('uses ScrollView for horizontal scrolling', () => {
      expect(content).toContain('ScrollView');
    });

    it('has All category', () => {
      expect(content).toContain('All');
    });

    it('has Restaurant category', () => {
      expect(content).toContain('Restaurant');
    });

    it('has Park category', () => {
      expect(content).toContain('Park');
    });

    it('has Cafe category', () => {
      expect(content).toContain('Cafe');
    });

    it('has Museum category', () => {
      expect(content).toContain('Museum');
    });

    it('has Bar category', () => {
      expect(content).toContain('Bar');
    });

    it('uses Pressable or TouchableOpacity for filter pills', () => {
      expect(content).toMatch(/Pressable|TouchableOpacity/);
    });

    it('has active filter highlighting (selected state styling)', () => {
      expect(content).toMatch(/active|selected|Active|Selected/);
    });

    it('exports CategoryFilter component', () => {
      expect(content).toMatch(
        /export\s+(const|function|default\s+function)\s+CategoryFilter/
      );
    });
  });

  // =========================================================================
  // 9. PlaceSummarySheet component
  // =========================================================================
  describe('components/map/PlaceSummarySheet.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'components/map/PlaceSummarySheet.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports BottomSheet from @gorhom/bottom-sheet', () => {
      expect(content).toContain('@gorhom/bottom-sheet');
      expect(content).toContain('BottomSheet');
    });

    it('shows place name', () => {
      expect(content).toMatch(/place.*name|name|placeName/);
    });

    it('shows busyness level text', () => {
      expect(content).toMatch(/busyness|Busyness|Quiet|Moderate|Busy/);
    });

    it('has View Details button', () => {
      expect(content).toContain('View Details');
    });

    it('navigates to /place/{id} on View Details press', () => {
      expect(content).toMatch(/\/place\//);
      expect(content).toContain('router');
    });

    it('imports expo-router for navigation', () => {
      expect(content).toContain('expo-router');
    });

    it('exports PlaceSummarySheet component', () => {
      expect(content).toMatch(
        /export\s+(const|function|default\s+function)\s+PlaceSummarySheet/
      );
    });

    it('fetches place detail to get popular_times data', () => {
      expect(content).toContain('getPlaceDetail');
      expect(content).toMatch(/useQuery|usePlaceDetail/);
    });

    it('has a MiniPopularTimesChart component for the current day', () => {
      expect(content).toContain('MiniPopularTimesChart');
      expect(content).toMatch(/popular_times|popularTimes/);
    });

    it('renders 24 hourly bars', () => {
      expect(content).toMatch(/hours\.map/);
      expect(content).toMatch(/24/);
    });

    it('colors bars by busyness level', () => {
      expect(content).toMatch(/getBarColor|BUSYNESS_COLORS/);
      expect(content).toMatch(/quiet|moderate|busy/);
    });

    it('highlights the current hour bar', () => {
      expect(content).toMatch(/currentHour|current_hour|isCurrentHour/);
      expect(content).toMatch(/getHours/);
    });

    it('shows day name label for the mini chart', () => {
      expect(content).toMatch(/Popular times/);
      expect(content).toMatch(/Mon|Tue|Wed|Thu|Fri|Sat|Sun/);
    });

    it('shows fallback when popular times data is unavailable', () => {
      expect(content).toMatch(/unavailable|No.*data/i);
    });
  });

  // =========================================================================
  // 10. Map Screen (index.tsx)
  // =========================================================================
  describe('app/(tabs)/index.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(tabs)/index.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports MapView or ClusteredMapView from react-native-map-clustering', () => {
      expect(content).toContain('react-native-map-clustering');
    });

    it('imports react-native-maps', () => {
      expect(content).toContain('react-native-maps');
    });

    it('imports PlacePin component', () => {
      expect(content).toContain('PlacePin');
    });

    it('imports CategoryFilter component', () => {
      expect(content).toContain('CategoryFilter');
    });

    it('imports PlaceSummarySheet component', () => {
      expect(content).toContain('PlaceSummarySheet');
    });

    it('imports useNearbyPlaces hook', () => {
      expect(content).toContain('useNearbyPlaces');
    });

    it('imports useLocationTracking hook', () => {
      expect(content).toContain('useLocationTracking');
    });

    it('has default location fallback (48.8566, 2.3522 Paris)', () => {
      expect(content).toContain('48.8566');
      expect(content).toContain('2.3522');
    });

    it('renders a full-screen MapView', () => {
      expect(content).toMatch(/MapView|ClusteredMapView/);
      expect(content).toMatch(/flex:\s*1|StyleSheet\.absoluteFillObject/);
    });

    it('has location permission denied guidance message', () => {
      expect(content).toMatch(/permission|Permission|location|Location/);
      expect(content).toMatch(/denied|grant|enable/i);
    });

    it('exports a default screen function', () => {
      expect(content).toMatch(/export\s+default\s+function/);
    });
  });

  // =========================================================================
  // 11. mapStore default region alignment
  // =========================================================================
  describe('stores/mapStore.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'stores/mapStore.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('default region uses Paris coordinates (48.8566, 2.3522) matching index.tsx', () => {
      expect(content).toContain('48.8566');
      expect(content).toContain('2.3522');
    });

    it('does not use Lyon coordinates (45.764, 4.8357)', () => {
      expect(content).not.toContain('45.764');
      expect(content).not.toContain('4.8357');
    });
  });
});
