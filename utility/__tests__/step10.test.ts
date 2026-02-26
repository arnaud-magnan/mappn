import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');

describe('Step 10: Build Place Detail Screen', () => {
  // =========================================================================
  // 1. usePlaceDetail hook
  // =========================================================================
  describe('hooks/usePlaceDetail.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'hooks/usePlaceDetail.ts');

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

    it('imports getPlaceDetail from placesService', () => {
      expect(content).toContain('getPlaceDetail');
      expect(content).toContain('placesService');
    });

    it('imports PlaceDetailResponse type', () => {
      expect(content).toContain('PlaceDetailResponse');
    });

    it('exports usePlaceDetail hook', () => {
      expect(content).toMatch(
        /export\s+(const|function)\s+usePlaceDetail/
      );
    });

    it('uses queryKey with places and id', () => {
      expect(content).toContain("'places'");
      expect(content).toContain('id');
    });

    it('sets staleTime to 5 minutes (STALE_TIME.PLACE_DETAIL or 300000)', () => {
      expect(content).toMatch(/STALE_TIME\.PLACE_DETAIL|300000|5\s*\*\s*60\s*\*\s*1000/);
    });

    it('calls getPlaceDetail with id', () => {
      expect(content).toMatch(/getPlaceDetail\(id\)/);
    });
  });

  // =========================================================================
  // 2. useForecast hook
  // =========================================================================
  describe('hooks/useForecast.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'hooks/useForecast.ts');

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

    it('imports getForecast from placesService', () => {
      expect(content).toContain('getForecast');
      expect(content).toContain('placesService');
    });

    it('imports ForecastResponse type', () => {
      expect(content).toContain('ForecastResponse');
    });

    it('exports useForecast hook', () => {
      expect(content).toMatch(
        /export\s+(const|function)\s+useForecast/
      );
    });

    it('uses queryKey with forecast, id, day, and hour', () => {
      expect(content).toContain("'forecast'");
      expect(content).toContain('id');
      expect(content).toContain('day');
      expect(content).toContain('hour');
    });

    it('sets staleTime to 1 minute (STALE_TIME.BUSYNESS or 60000)', () => {
      expect(content).toMatch(/STALE_TIME\.BUSYNESS|60000|1\s*\*\s*60\s*\*\s*1000/);
    });

    it('enabled only when day and hour are defined', () => {
      expect(content).toContain('enabled');
      expect(content).toMatch(/day\s*!==\s*undefined|day\s*!=\s*null/);
      expect(content).toMatch(/hour\s*!==\s*undefined|hour\s*!=\s*null/);
    });

    it('calls getForecast with id, day, and hour', () => {
      expect(content).toMatch(/getForecast\(id,\s*day/);
    });
  });

  // =========================================================================
  // 3. BusynessHistogram component
  // =========================================================================
  describe('components/place/BusynessHistogram.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'components/place/BusynessHistogram.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports BarChart from react-native-gifted-charts', () => {
      expect(content).toContain('BarChart');
      expect(content).toContain('react-native-gifted-charts');
    });

    it('imports BusynessData type', () => {
      expect(content).toContain('BusynessData');
    });

    it('imports BUSYNESS_COLORS', () => {
      expect(content).toContain('BUSYNESS_COLORS');
    });

    it('exports BusynessHistogram component', () => {
      expect(content).toMatch(
        /export\s+(const|function|default\s+function)\s+BusynessHistogram/
      );
    });

    it('renders 24 bars from hours array', () => {
      // The component maps over hours to build bar data
      expect(content).toMatch(/hours|\.map/);
      expect(content).toMatch(/24|hours\.length/);
    });

    it('has day selector with 7 days Mon-Sun', () => {
      expect(content).toContain('Mon');
      expect(content).toContain('Sun');
      expect(content).toMatch(/Tue|Tue/);
      expect(content).toMatch(/Wed|Wed/);
      expect(content).toMatch(/Thu|Thu/);
      expect(content).toMatch(/Fri|Fri/);
      expect(content).toMatch(/Sat|Sat/);
    });

    it('uses state for selected day', () => {
      expect(content).toMatch(/selectedDay|setSelectedDay/);
    });

    it('colors bars by busyness level (green/yellow/red)', () => {
      expect(content).toMatch(/#22c55e|quiet|BUSYNESS_COLORS\.quiet/);
      expect(content).toMatch(/#eab308|moderate|BUSYNESS_COLORS\.moderate/);
      expect(content).toMatch(/#ef4444|busy|BUSYNESS_COLORS\.busy/);
    });

    it('highlights current hour bar', () => {
      expect(content).toMatch(/currentHour|new Date|getHours/);
    });

    it('has props for popular_times data', () => {
      expect(content).toMatch(/popular_times|popularTimes|data/);
    });
  });

  // =========================================================================
  // 4. LiveBusynessIndicator component
  // =========================================================================
  describe('components/place/LiveBusynessIndicator.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'components/place/LiveBusynessIndicator.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports BUSYNESS_COLORS', () => {
      expect(content).toContain('BUSYNESS_COLORS');
    });

    it('exports LiveBusynessIndicator component', () => {
      expect(content).toMatch(
        /export\s+(const|function|default\s+function)\s+LiveBusynessIndicator/
      );
    });

    it('shows busyness value when available', () => {
      expect(content).toMatch(/current_popularity|currentPopularity|value/);
    });

    it('shows labels Quiet, Moderate, or Busy', () => {
      expect(content).toContain('Quiet');
      expect(content).toContain('Moderate');
      expect(content).toContain('Busy');
    });

    it('shows "No live data" when value is null/undefined', () => {
      expect(content).toMatch(/No live data/);
    });

    it('uses color-coded badge', () => {
      expect(content).toMatch(/badge|Badge/);
      expect(content).toMatch(/backgroundColor|background/);
    });
  });

  // =========================================================================
  // 5. ForecastSlider component
  // =========================================================================
  describe('components/place/ForecastSlider.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'components/place/ForecastSlider.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports useForecast hook', () => {
      expect(content).toContain('useForecast');
    });

    it('imports BUSYNESS_COLORS', () => {
      expect(content).toContain('BUSYNESS_COLORS');
    });

    it('exports ForecastSlider component', () => {
      expect(content).toMatch(
        /export\s+(const|function|default\s+function)\s+ForecastSlider/
      );
    });

    it('has day picker with Mon-Sun', () => {
      expect(content).toContain('Mon');
      expect(content).toContain('Sun');
    });

    it('has hour picker/selector (0-23)', () => {
      expect(content).toMatch(/hour|Hour/);
      expect(content).toMatch(/0|23/);
    });

    it('displays predicted busyness', () => {
      expect(content).toMatch(/predicted_busyness|predictedBusyness|forecast/i);
    });

    it('uses color coding for forecast result', () => {
      expect(content).toMatch(/BUSYNESS_COLORS|busynessColor|getBusynessLevel/);
    });

    it('accepts placeId prop', () => {
      expect(content).toMatch(/placeId|place_id/);
    });
  });

  // =========================================================================
  // 6. VisitHistoryList component
  // =========================================================================
  describe('components/place/VisitHistoryList.tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'components/place/VisitHistoryList.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports FlatList from react-native', () => {
      expect(content).toContain('FlatList');
      expect(content).toContain('react-native');
    });

    it('imports VisitResponse type', () => {
      expect(content).toContain('VisitResponse');
    });

    it('exports VisitHistoryList component', () => {
      expect(content).toMatch(
        /export\s+(const|function|default\s+function)\s+VisitHistoryList/
      );
    });

    it('shows date for each visit', () => {
      expect(content).toMatch(/started_at|date|Date|toLocaleDateString/);
    });

    it('shows duration for each visit', () => {
      expect(content).toMatch(/duration|Duration|duration_seconds/);
    });

    it('renders visit items', () => {
      expect(content).toMatch(/renderItem|keyExtractor/);
    });
  });

  // =========================================================================
  // 7. Place Detail Screen
  // =========================================================================
  describe('app/place/[id].tsx', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/place/[id].tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it('imports usePlaceDetail hook', () => {
      expect(content).toContain('usePlaceDetail');
    });

    it('imports ScrollView from react-native', () => {
      expect(content).toContain('ScrollView');
    });

    it('imports BusynessHistogram component', () => {
      expect(content).toContain('BusynessHistogram');
    });

    it('imports LiveBusynessIndicator component', () => {
      expect(content).toContain('LiveBusynessIndicator');
    });

    it('imports ForecastSlider component', () => {
      expect(content).toContain('ForecastSlider');
    });

    it('imports VisitHistoryList component', () => {
      expect(content).toContain('VisitHistoryList');
    });

    it('imports LoadingSpinner component', () => {
      expect(content).toContain('LoadingSpinner');
    });

    it('uses expo-router for id param extraction', () => {
      expect(content).toContain('expo-router');
      expect(content).toMatch(/useLocalSearchParams|useGlobalSearchParams/);
    });

    it('displays place name', () => {
      expect(content).toMatch(/place.*name|data.*name|\.name/);
    });

    it('displays place category', () => {
      expect(content).toMatch(/category/);
    });

    it('displays place address', () => {
      expect(content).toMatch(/address/);
    });

    it('displays place city', () => {
      expect(content).toMatch(/city/);
    });

    it('shows loading state', () => {
      expect(content).toMatch(/isLoading|isPending/);
      expect(content).toContain('LoadingSpinner');
    });

    it('shows placeholder when no busyness data', () => {
      expect(content).toMatch(/busyness_data|busynessData/);
      expect(content).toMatch(/not.*available|unavailable|No busyness|not yet/i);
    });

    it('has back navigation', () => {
      expect(content).toMatch(/router\.back|router\.push|goBack|Back/);
    });

    it('exports a default screen function', () => {
      expect(content).toMatch(/export\s+default\s+function/);
    });

    it('renders BusynessHistogram when busyness_data available', () => {
      expect(content).toContain('BusynessHistogram');
      expect(content).toMatch(/busyness_data/);
    });

    it('renders ForecastSlider when busyness_data available', () => {
      expect(content).toContain('ForecastSlider');
    });

    it('conditionally renders busyness components based on data availability', () => {
      // Should check for busyness_data before rendering histogram/forecast
      expect(content).toMatch(/busyness_data\s*&&|busyness_data\s*\?|busyness_data\s*!==\s*null/);
    });
  });
});
