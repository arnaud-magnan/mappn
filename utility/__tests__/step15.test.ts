import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');

describe('Step 15: Polish -- Empty States, Error Handling, Accessibility', () => {
  // =========================================================================
  // 1. NetworkBanner integration in root layout
  // =========================================================================
  describe('NetworkBanner in root layout (_layout.tsx)', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/_layout.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('imports NetworkBanner component', () => {
      expect(content).toContain('NetworkBanner');
    });

    it('renders NetworkBanner in the layout tree', () => {
      expect(content).toMatch(/<NetworkBanner/);
    });
  });

  // =========================================================================
  // 2. Journal empty state text matches spec exactly
  // =========================================================================
  describe('Journal empty state', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(tabs)/journal.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('shows "Visit places to start your journal!" when no visits exist', () => {
      expect(content).toContain('Visit places to start your journal!');
    });

    it('uses LoadingSpinner for loading state', () => {
      expect(content).toContain('LoadingSpinner');
      expect(content).toContain('isLoading');
    });

    it('has error handling for failed API calls', () => {
      expect(content).toContain('isError');
    });
  });

  // =========================================================================
  // 3. Explore empty state text matches spec
  // =========================================================================
  describe('Explore empty state', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(tabs)/explore.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('shows "Start exploring to see your heatmap!" when no visits exist', () => {
      expect(content).toContain('Start exploring to see your heatmap!');
    });

    it('uses LoadingSpinner for loading state', () => {
      expect(content).toContain('LoadingSpinner');
      expect(content).toContain('isLoading');
    });

    it('has error handling for failed API calls', () => {
      expect(content).toContain('isError');
    });
  });

  // =========================================================================
  // 4. Profile empty state text matches spec
  // =========================================================================
  describe('Profile empty state', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(tabs)/profile.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('shows "Start exploring to track your stats!" when no visits exist', () => {
      expect(content).toContain('Start exploring to track your stats!');
    });

    it('uses LoadingSpinner for loading state', () => {
      expect(content).toContain('LoadingSpinner');
      expect(content).toContain('isLoading');
    });

    it('has error handling for failed API calls', () => {
      expect(content).toContain('isError');
    });

    it('city passports shows "Visit a city to earn stamps!" when no cities visited', () => {
      expect(content).toContain('Visit a city to earn stamps!');
    });
  });

  // =========================================================================
  // 5. City passport empty state
  // =========================================================================
  describe('City passport empty state', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/passport/[city].tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('uses LoadingSpinner for loading state', () => {
      expect(content).toContain('LoadingSpinner');
      expect(content).toContain('isLoading');
    });

    it('has error handling', () => {
      expect(content).toContain('error');
    });
  });

  // =========================================================================
  // 6. Place detail no busyness data placeholder
  // =========================================================================
  describe('Place detail no busyness data', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/place/[id].tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('shows "Busyness data not yet available" for places without busyness_data', () => {
      expect(content).toContain('Busyness data not yet available');
    });

    it('uses LoadingSpinner for loading state', () => {
      expect(content).toContain('LoadingSpinner');
      expect(content).toContain('isLoading');
    });

    it('has error handling for failed API calls', () => {
      expect(content).toContain('isError');
    });
  });

  // =========================================================================
  // 7. Map permission denied guidance
  // =========================================================================
  describe('Map permission denied guidance', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(tabs)/index.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('shows guidance message when location permission is denied', () => {
      expect(content).toMatch(/permissionGranted|permission/i);
      expect(content).toMatch(/location.*permission|permission.*denied/i);
    });

    it('centers map on default location (Paris)', () => {
      expect(content).toContain('48.8566');
      expect(content).toContain('2.3522');
    });

    it('uses LoadingSpinner while checking permission', () => {
      expect(content).toContain('LoadingSpinner');
    });
  });

  // =========================================================================
  // 8. PlacePin shape/icon differentiation by busyness level
  // =========================================================================
  describe('PlacePin shape/icon differentiation', () => {
    let content: string;
    const filePath = path.join(ROOT, 'components/map/PlacePin.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('has a function or mapping that returns different shapes per busyness level', () => {
      // There must be a function or constant that maps busyness levels to distinct shapes/icons
      expect(content).toMatch(/getPinShape|getPinIcon|PIN_SHAPES|PIN_ICONS|pinConfig/i);
    });

    it('uses MaterialIcons for visual differentiation', () => {
      expect(content).toContain('MaterialIcons');
    });

    it('exports getBusynessLevel and getBusynessLabel', () => {
      expect(content).toContain('getBusynessLevel');
      expect(content).toContain('getBusynessLabel');
    });
  });

  // =========================================================================
  // 9. LiveBusynessIndicator text labels
  // =========================================================================
  describe('LiveBusynessIndicator text labels', () => {
    let content: string;
    const filePath = path.join(ROOT, 'components/place/LiveBusynessIndicator.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('displays "Quiet" label', () => {
      expect(content).toContain('Quiet');
    });

    it('displays "Moderate" label', () => {
      expect(content).toContain('Moderate');
    });

    it('displays "Busy" label', () => {
      expect(content).toContain('Busy');
    });
  });

  // =========================================================================
  // 10. PlaceSummarySheet busyness text labels
  // =========================================================================
  describe('PlaceSummarySheet busyness text labels', () => {
    let content: string;
    const filePath = path.join(ROOT, 'components/map/PlaceSummarySheet.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('displays busyness label text in badge', () => {
      expect(content).toContain('busynessLabel');
      expect(content).toContain('getBusynessLabel');
    });

    it('imports getBusynessLabel from PlacePin', () => {
      expect(content).toContain('getBusynessLabel');
    });
  });

  // =========================================================================
  // 11. Session expired redirect message
  // =========================================================================
  describe('Token refresh failure redirect', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/(auth)/login.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('shows "Session expired, please log in again" when session expired', () => {
      expect(content).toContain('Session expired, please log in again');
    });

    it('checks sessionExpired flag from auth store', () => {
      expect(content).toContain('sessionExpired');
    });
  });

  // =========================================================================
  // 12. TanStack Query cache preserves data during network loss
  // =========================================================================
  describe('TanStack Query cache configuration', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/_layout.tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('creates QueryClient with staleTime for caching', () => {
      expect(content).toContain('QueryClient');
      expect(content).toContain('staleTime');
    });

    it('wraps app in QueryClientProvider', () => {
      expect(content).toContain('QueryClientProvider');
    });
  });
});
