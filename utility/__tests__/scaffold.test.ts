import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');

describe('Project Scaffold', () => {
  describe('Directory structure', () => {
    const requiredDirectories = [
      'app/(auth)',
      'app/(tabs)',
      'app/place',
      'app/journal',
      'app/passport',
      'components/map',
      'components/place',
      'components/explore',
      'components/journal',
      'components/profile',
      'components/ui',
      'services',
      'stores',
      'hooks',
      'types',
      'constants',
    ];

    it.each(requiredDirectories)('has %s directory', (dir) => {
      const fullPath = path.join(ROOT, dir);
      expect(fs.existsSync(fullPath)).toBe(true);
      expect(fs.statSync(fullPath).isDirectory()).toBe(true);
    });
  });

  describe('Tab screens', () => {
    const tabScreens = [
      'app/(tabs)/index.tsx',
      'app/(tabs)/explore.tsx',
      'app/(tabs)/journal.tsx',
      'app/(tabs)/profile.tsx',
      'app/(tabs)/_layout.tsx',
    ];

    it.each(tabScreens)('has %s file', (file) => {
      const fullPath = path.join(ROOT, file);
      expect(fs.existsSync(fullPath)).toBe(true);
    });

    it('does not have old template tab files', () => {
      expect(fs.existsSync(path.join(ROOT, 'app/(tabs)/two.tsx'))).toBe(false);
    });

    it('does not have old modal screen', () => {
      expect(fs.existsSync(path.join(ROOT, 'app/modal.tsx'))).toBe(false);
    });
  });

  describe('Dependencies', () => {
    let packageJson: Record<string, unknown>;

    beforeAll(() => {
      const raw = fs.readFileSync(path.join(ROOT, 'package.json'), 'utf-8');
      packageJson = JSON.parse(raw);
    });

    const requiredDependencies = [
      'react-native-maps',
      'expo-location',
      '@tanstack/react-query',
      'zustand',
      'axios',
      'expo-secure-store',
      'expo-image-picker',
      'expo-image',
      'expo-sharing',
      'react-native-view-shot',
      '@gorhom/bottom-sheet',
      'react-native-gifted-charts',
      'react-native-map-clustering',
      '@react-native-async-storage/async-storage',
      '@react-native-community/netinfo',
    ];

    it.each(requiredDependencies)('has %s installed', (dep) => {
      const deps = packageJson.dependencies as Record<string, string>;
      expect(deps).toHaveProperty(dep);
    });
  });

  describe('Configuration', () => {
    it('tsconfig.json has strict mode enabled', () => {
      const raw = fs.readFileSync(path.join(ROOT, 'tsconfig.json'), 'utf-8');
      const tsconfig = JSON.parse(raw);
      expect(tsconfig.compilerOptions.strict).toBe(true);
    });

    it('eas.json has development, preview, and production profiles', () => {
      const raw = fs.readFileSync(path.join(ROOT, 'eas.json'), 'utf-8');
      const easConfig = JSON.parse(raw);
      expect(easConfig.build).toHaveProperty('development');
      expect(easConfig.build).toHaveProperty('preview');
      expect(easConfig.build).toHaveProperty('production');
    });

    it('app.config.ts has expo-location plugin', () => {
      const content = fs.readFileSync(path.join(ROOT, 'app.config.ts'), 'utf-8');
      expect(content).toContain('expo-location');
      expect(content).toContain('locationWhenInUsePermission');
    });

    it('app.config.ts has expo-image-picker plugin', () => {
      const content = fs.readFileSync(path.join(ROOT, 'app.config.ts'), 'utf-8');
      expect(content).toContain('expo-image-picker');
      expect(content).toContain('photosPermission');
      expect(content).toContain('cameraPermission');
    });

    it('app.config.ts has Google Maps API key config for Android', () => {
      const content = fs.readFileSync(path.join(ROOT, 'app.config.ts'), 'utf-8');
      expect(content).toContain('googleMaps');
      expect(content).toContain('GOOGLE_MAPS_ANDROID_KEY');
    });
  });

  describe('Tab layout configuration', () => {
    it('tab layout defines 4 tabs: Map, Explore, Journal, Profile', () => {
      const content = fs.readFileSync(
        path.join(ROOT, 'app/(tabs)/_layout.tsx'),
        'utf-8'
      );
      expect(content).toContain("title: 'Map'");
      expect(content).toContain("title: 'Explore'");
      expect(content).toContain("title: 'Journal'");
      expect(content).toContain("title: 'Profile'");
    });

    it('tab layout uses MaterialIcons', () => {
      const content = fs.readFileSync(
        path.join(ROOT, 'app/(tabs)/_layout.tsx'),
        'utf-8'
      );
      expect(content).toContain('MaterialIcons');
      expect(content).toContain("name=\"map\"");
      expect(content).toContain("name=\"explore\"");
      expect(content).toContain("name=\"book\"");
      expect(content).toContain("name=\"person\"");
    });
  });
});
