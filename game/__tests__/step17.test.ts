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
});
