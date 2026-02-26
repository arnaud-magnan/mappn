import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');

describe('Step 17: Map Claiming UX', () => {
  // =========================================================================
  // Task 1: LootIndicator uses React Native Animated (not Reanimated)
  // =========================================================================
  describe('components/map/LootIndicator.tsx', () => {
    let content: string;
    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'components/map/LootIndicator.tsx'),
        'utf-8'
      );
    });

    it('does NOT import from react-native-reanimated', () => {
      expect(content).not.toContain("from 'react-native-reanimated'");
    });

    it('imports Animated from react-native', () => {
      expect(content).toContain("Animated");
      expect(content).toContain("from 'react-native'");
    });

    it('uses Animated.loop for pulse animation', () => {
      expect(content).toContain('Animated.loop');
    });

    it('uses useRef for Animated.Value', () => {
      expect(content).toContain('useRef(new Animated.Value');
    });

    it('uses tracksViewChanges prop on Marker', () => {
      expect(content).toContain('tracksViewChanges={tracksViewChanges}');
    });
  });

  // =========================================================================
  // Task 2: locationStore has ClaimingState
  // =========================================================================
  describe('stores/locationStore.ts', () => {
    let content: string;
    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'stores/locationStore.ts'),
        'utf-8'
      );
    });

    it('exports ClaimingState interface', () => {
      expect(content).toMatch(/export\s+interface\s+ClaimingState/);
    });

    it('ClaimingState has placeId, placeName, startedAt', () => {
      expect(content).toContain('placeId: number');
      expect(content).toContain('placeName: string');
      expect(content).toContain('startedAt: number');
    });

    it('LocationState has claimingState field', () => {
      expect(content).toContain('claimingState: ClaimingState | null');
    });

    it('LocationState has setClaimingState action', () => {
      expect(content).toContain('setClaimingState:');
    });
  });

  // =========================================================================
  // Task 3: useLocationTracking manages claimingState
  // =========================================================================
  describe('hooks/useLocationTracking.ts', () => {
    let content: string;
    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'hooks/useLocationTracking.ts'),
        'utf-8'
      );
    });

    it('reads setClaimingState from locationStore', () => {
      expect(content).toContain('setClaimingState');
    });

    it('calls setClaimingState when nearby_places is non-empty', () => {
      expect(content).toContain('nearby_places');
      expect(content).toContain('setClaimingState({');
    });

    it('clears claimingState when nearby_places is empty', () => {
      expect(content).toContain('setClaimingState(null)');
    });

    it('preserves startedAt when same place is already being tracked', () => {
      expect(content).toContain('claimingState');
      expect(content).toContain('placeId');
    });
  });

  // =========================================================================
  // Task 4: GeofenceCircle component
  // =========================================================================
  describe('components/map/GeofenceCircle.tsx', () => {
    let content: string;
    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'components/map/GeofenceCircle.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(path.join(ROOT, 'components/map/GeofenceCircle.tsx'))
      ).toBe(true);
    });

    it('imports Circle from react-native-maps', () => {
      expect(content).toContain("{ Circle }");
      expect(content).toContain("from 'react-native-maps'");
    });

    it('uses radius 75 (matching backend geofence_radius_m)', () => {
      expect(content).toContain('radius={75}');
    });

    it('exports GeofenceCircle component', () => {
      expect(content).toMatch(/export.*GeofenceCircle/);
    });
  });

  // =========================================================================
  // Task 5: ClaimingProgressHUD component
  // =========================================================================
  describe('components/map/ClaimingProgressHUD.tsx', () => {
    let content: string;
    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'components/map/ClaimingProgressHUD.tsx'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(path.join(ROOT, 'components/map/ClaimingProgressHUD.tsx'))
      ).toBe(true);
    });

    it('exports ClaimingProgressHUD component', () => {
      expect(content).toMatch(/export.*ClaimingProgressHUD/);
    });

    it('accepts placeName and startedAt props', () => {
      expect(content).toContain('placeName');
      expect(content).toContain('startedAt');
    });

    it('updates progress with setInterval', () => {
      expect(content).toContain('setInterval');
      expect(content).toContain('clearInterval');
    });

    it('uses VISIT_MIN_DURATION_MS of 300_000 for progress calculation', () => {
      // 5 minutes = 300 000 ms (mirrors backend visit_min_duration_seconds = 300)
      expect(content).toContain('300_000');
    });

    it('renders Unlocking text', () => {
      expect(content).toContain('Unlocking');
    });

    it('is absolutely positioned', () => {
      expect(content).toContain("position: 'absolute'");
    });
  });

  // =========================================================================
  // Task 6: MapScreen wires GeofenceCircle + ClaimingProgressHUD
  // =========================================================================
  describe('app/(tabs)/index.tsx', () => {
    let content: string;
    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'app/(tabs)/index.tsx'),
        'utf-8'
      );
    });

    it('imports GeofenceCircle', () => {
      expect(content).toContain('GeofenceCircle');
    });

    it('imports ClaimingProgressHUD', () => {
      expect(content).toContain('ClaimingProgressHUD');
    });

    it('reads claimingState from locationStore', () => {
      expect(content).toContain('claimingState');
    });

    it('renders GeofenceCircle inside MapView when claiming', () => {
      expect(content).toContain('<GeofenceCircle');
    });

    it('renders ClaimingProgressHUD outside MapView when claiming', () => {
      expect(content).toContain('<ClaimingProgressHUD');
    });
  });
});
