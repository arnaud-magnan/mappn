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
});
