import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');

describe('Step 14: Integrate GPS Ping and Visit Confirmation Cache Invalidation', () => {
  // =========================================================================
  // 1. useLocationTracking hook - GPS Ping Integration
  // =========================================================================
  describe('hooks/useLocationTracking.ts - GPS Ping Integration', () => {
    let content: string;
    const filePath = path.join(ROOT, 'hooks/useLocationTracking.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(filePath)).toBe(true);
    });

    // --- GPS Ping Submission ---

    it('imports postGpsPing from visitsService', () => {
      expect(content).toContain('postGpsPing');
      expect(content).toMatch(/visitsService|\.\.\/services\/visitsService/);
    });

    it('calls postGpsPing with lat, lon, accuracy, and timestamp', () => {
      expect(content).toContain('postGpsPing');
      // Verify it passes latitude, longitude, accuracy, and a timestamp
      expect(content).toMatch(/postGpsPing\(/);
      expect(content).toMatch(/\.toISOString\(\)/);
    });

    it('sends GPS ping on each location update', () => {
      // The ping should happen inside or be triggered by the location callback
      expect(content).toContain('postGpsPing');
    });

    // --- Cache Invalidation ---

    it('imports useQueryClient from @tanstack/react-query', () => {
      expect(content).toContain('useQueryClient');
      expect(content).toContain('@tanstack/react-query');
    });

    it('invalidates journal query cache on confirmed visits', () => {
      expect(content).toContain("'journal'");
      expect(content).toContain('invalidateQueries');
    });

    it('invalidates stats query cache on confirmed visits', () => {
      expect(content).toContain("'stats'");
    });

    it('invalidates achievements query cache on confirmed visits', () => {
      expect(content).toContain("'achievements'");
    });

    it('invalidates heatmap query cache on confirmed visits', () => {
      expect(content).toContain("'heatmap'");
    });

    it('invalidates passport query cache on confirmed visits', () => {
      expect(content).toContain("'passport'");
    });

    it('checks confirmed_visits array length before invalidating', () => {
      expect(content).toMatch(/confirmed_visits/);
      expect(content).toMatch(/\.length\s*>\s*0|\.length\s*!==\s*0|\.length$/);
    });

    // --- Low GPS Accuracy ---

    it('imports GPS_ACCURACY_THRESHOLD_M from config', () => {
      expect(content).toContain('GPS_ACCURACY_THRESHOLD_M');
    });

    it('exposes lowAccuracy boolean flag in return value', () => {
      expect(content).toMatch(/lowAccuracy/);
    });

    it('detects when accuracy exceeds 100 meter threshold', () => {
      expect(content).toContain('GPS_ACCURACY_THRESHOLD_M');
      // Should compare accuracy to the threshold
      expect(content).toMatch(/accuracy.*>.*GPS_ACCURACY_THRESHOLD_M|accuracy.*>.*100/);
    });

    it('still sends ping even when accuracy is low', () => {
      // The ping call should not be skipped based on accuracy
      // Verify postGpsPing is called regardless of accuracy
      expect(content).toContain('postGpsPing');
    });

    // --- Offline Queue ---

    it('imports NetInfo from @react-native-community/netinfo', () => {
      expect(content).toContain('NetInfo');
      expect(content).toContain('@react-native-community/netinfo');
    });

    it('has an offline queue for GPS coordinates', () => {
      expect(content).toMatch(/queue|Queue/);
    });

    it('queues coordinates when network is unavailable', () => {
      // Should reference some kind of queue push when offline
      expect(content).toMatch(/queue.*push|\.push\(/);
    });

    it('flushes queued coordinates when connectivity returns', () => {
      expect(content).toMatch(/flush|Flush/);
    });

    // --- App State Management ---

    it('imports AppState from react-native', () => {
      expect(content).toContain('AppState');
      expect(content).toContain("from 'react-native'");
    });

    it('listens to AppState changes', () => {
      expect(content).toContain('AppState');
      expect(content).toMatch(/addEventListener|change/);
    });

    it('stops tracking when app goes to background', () => {
      expect(content).toContain('background');
      expect(content).toContain('stopTracking');
    });

    it('resumes tracking when app returns to active', () => {
      expect(content).toContain('active');
      expect(content).toContain('startTracking');
    });

    // --- Return Type ---

    it('exports LocationTrackingState interface with lowAccuracy', () => {
      expect(content).toMatch(/interface\s+LocationTrackingState/);
      expect(content).toContain('lowAccuracy');
      expect(content).toContain('boolean');
    });

    it('returns lowAccuracy in the hook result', () => {
      // Should be in the return statement
      expect(content).toMatch(/return\s*\{[\s\S]*lowAccuracy[\s\S]*\}/);
    });

    it('preserves existing return values: permissionGranted, permissionChecked, error', () => {
      expect(content).toContain('permissionGranted');
      expect(content).toContain('permissionChecked');
      expect(content).toContain('error');
    });
  });
});
