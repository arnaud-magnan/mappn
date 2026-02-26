import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');

describe('Step 6: Types, Constants, API Client, Auth Store, Utility Service', () => {
  describe('types/api.ts', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(path.join(ROOT, 'types/api.ts'), 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(path.join(ROOT, 'types/api.ts'))).toBe(true);
    });

    const requiredInterfaces = [
      'PlaceResponse',
      'PlaceDetailResponse',
      'BusynessData',
      'ForecastResponse',
      'GPSPingResponse',
      'VisitResponse',
      'UserStatsResponse',
      'AchievementResponse',
      'JournalEntryResponse',
      'HeatmapAreaResponse',
      'HeatmapResponse',
      'CityPassportResponse',
      'AuthTokenResponse',
      'UserResponse',
    ];

    it.each(requiredInterfaces)('exports %s interface', (name) => {
      expect(content).toMatch(new RegExp(`export\\s+interface\\s+${name}\\s*\\{`));
    });

    it('BusynessData has popular_times with day and hours', () => {
      expect(content).toContain('popular_times');
      expect(content).toContain('day: number');
      expect(content).toContain('hours: number[]');
    });

    it('BusynessData has optional current_popularity', () => {
      expect(content).toContain('current_popularity');
    });

    it('BusynessData has optional time_spent tuple', () => {
      expect(content).toContain('time_spent');
      expect(content).toContain('[number, number]');
    });

    it('PlaceResponse has required fields from backend schema', () => {
      expect(content).toContain('id: number');
      expect(content).toContain('name: string');
      expect(content).toContain('category: string');
      expect(content).toContain('lat: number');
      expect(content).toContain('lon: number');
      expect(content).toContain('current_busyness');
      expect(content).toContain('busyness_stale');
    });

    it('AuthTokenResponse has token fields', () => {
      expect(content).toContain('access_token: string');
      expect(content).toContain('refresh_token: string');
      expect(content).toContain('token_type: string');
      expect(content).toContain('expires_in: number');
    });

    it('UserResponse has user fields', () => {
      expect(content).toContain('username: string');
      expect(content).toContain('email: string');
    });

    it('AchievementResponse has progress tracking fields', () => {
      expect(content).toContain('progress: number');
      expect(content).toContain('threshold: number');
      expect(content).toContain('earned: boolean');
    });

    it('HeatmapResponse has areas and explored_pct', () => {
      expect(content).toContain('areas: HeatmapAreaResponse[]');
      expect(content).toContain('explored_pct: number');
    });

    it('CityPassportResponse has stamps and badge_earned', () => {
      expect(content).toContain('stamps: PassportStampResponse[]');
      expect(content).toContain('badge_earned: boolean');
    });
  });

  describe('constants/colors.ts', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(path.join(ROOT, 'constants/colors.ts'), 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(path.join(ROOT, 'constants/colors.ts'))).toBe(true);
    });

    it('exports BUSYNESS_COLORS', () => {
      expect(content).toContain('BUSYNESS_COLORS');
    });

    it('has quiet color #22c55e', () => {
      expect(content).toContain('#22c55e');
    });

    it('has moderate color #eab308', () => {
      expect(content).toContain('#eab308');
    });

    it('has busy color #ef4444', () => {
      expect(content).toContain('#ef4444');
    });

    it('has noData color #9ca3af', () => {
      expect(content).toContain('#9ca3af');
    });
  });

  describe('constants/config.ts', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(path.join(ROOT, 'constants/config.ts'), 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(path.join(ROOT, 'constants/config.ts'))).toBe(true);
    });

    it('exports API_BASE_URL from EXPO_PUBLIC_API_URL env var', () => {
      expect(content).toContain('API_BASE_URL');
      expect(content).toContain('EXPO_PUBLIC_API_URL');
    });

    it('exports GPS_INTERVAL_MS as 15000', () => {
      expect(content).toContain('GPS_INTERVAL_MS');
      expect(content).toContain('15000');
    });

    it('exports stale time constants', () => {
      expect(content).toContain('STALE_TIME');
    });
  });

  describe('constants/achievements.ts', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'constants/achievements.ts'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(path.join(ROOT, 'constants/achievements.ts'))
      ).toBe(true);
    });

    it('exports ACHIEVEMENT_DEFINITIONS', () => {
      expect(content).toContain('ACHIEVEMENT_DEFINITIONS');
    });

    const requiredAchievements = [
      { id: 'wanderer', name: 'Wanderer', threshold: '10' },
      { id: 'globe_trotter', name: 'Globe Trotter', threshold: '5' },
      { id: 'night_owl', name: 'Night Owl', threshold: '10' },
      { id: 'early_bird', name: 'Early Bird', threshold: '10' },
      { id: 'foodie', name: 'Foodie', threshold: '50' },
      { id: 'culture_vulture', name: 'Culture Vulture', threshold: '20' },
    ];

    it.each(requiredAchievements)(
      'has achievement %s with threshold %s',
      ({ id, name, threshold }) => {
        expect(content).toContain(id);
        expect(content).toContain(name);
        expect(content).toContain(threshold);
      }
    );

    it('has 3 categories: explorer, habits, categories', () => {
      expect(content).toContain('explorer');
      expect(content).toContain('habits');
      expect(content).toContain('categories');
    });
  });

  describe('services/api.ts', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(path.join(ROOT, 'services/api.ts'), 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(path.join(ROOT, 'services/api.ts'))).toBe(true);
    });

    it('imports axios', () => {
      expect(content).toContain('axios');
    });

    it('imports SecureStore from expo-secure-store', () => {
      expect(content).toContain('expo-secure-store');
    });

    it('creates axios instance with baseURL from config', () => {
      expect(content).toContain('axios.create');
      expect(content).toContain('baseURL');
    });

    it('has request interceptor for Bearer token', () => {
      expect(content).toContain('interceptors.request');
      expect(content).toContain('Bearer');
      expect(content).toContain('access_token');
    });

    it('has response interceptor for 401 handling', () => {
      expect(content).toContain('interceptors.response');
      expect(content).toContain('401');
    });

    it('handles token refresh on 401', () => {
      expect(content).toContain('/auth/refresh');
      expect(content).toContain('refresh_token');
    });

    it('clears auth on refresh failure', () => {
      expect(content).toContain('clearAuth');
    });

    it('exports the api instance', () => {
      expect(content).toMatch(/export\s+(const|default)/);
    });
  });

  describe('stores/authStore.ts', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(path.join(ROOT, 'stores/authStore.ts'), 'utf-8');
    });

    it('file exists', () => {
      expect(fs.existsSync(path.join(ROOT, 'stores/authStore.ts'))).toBe(true);
    });

    it('imports zustand create', () => {
      expect(content).toContain('zustand');
      expect(content).toContain('create');
    });

    it('imports expo-secure-store', () => {
      expect(content).toContain('expo-secure-store');
    });

    it('has user state', () => {
      expect(content).toContain('user');
    });

    it('has isAuthenticated state', () => {
      expect(content).toContain('isAuthenticated');
    });

    it('has accessToken state', () => {
      expect(content).toContain('accessToken');
    });

    it('has refreshToken state', () => {
      expect(content).toContain('refreshToken');
    });

    it('has setTokens method', () => {
      expect(content).toContain('setTokens');
    });

    it('has clearAuth method', () => {
      expect(content).toContain('clearAuth');
    });

    it('has loadTokens method that reads from SecureStore', () => {
      expect(content).toContain('loadTokens');
      expect(content).toContain('getItemAsync');
    });

    it('has setUser method', () => {
      expect(content).toContain('setUser');
    });

    it('stores tokens in SecureStore (setItemAsync)', () => {
      expect(content).toContain('setItemAsync');
    });

    it('deletes tokens from SecureStore on clearAuth (deleteItemAsync)', () => {
      expect(content).toContain('deleteItemAsync');
    });

    it('does NOT use AsyncStorage for tokens', () => {
      expect(content).not.toContain('AsyncStorage');
    });
  });

  describe('services/utilityService.ts', () => {
    let content: string;

    beforeAll(() => {
      content = fs.readFileSync(
        path.join(ROOT, 'services/utilityService.ts'),
        'utf-8'
      );
    });

    it('file exists', () => {
      expect(
        fs.existsSync(path.join(ROOT, 'services/utilityService.ts'))
      ).toBe(true);
    });

    it('imports api instance', () => {
      expect(content).toContain("from './api'");
    });

    const requiredFunctions = [
      'getUserStats',
      'getAchievements',
      'getJournal',
      'addJournalNote',
      'getHeatmap',
      'getCityPassport',
    ];

    it.each(requiredFunctions)('exports %s function', (fnName) => {
      expect(content).toContain(fnName);
      expect(content).toMatch(new RegExp(`export\\s+(const|async\\s+function|function)\\s+${fnName}`));
    });

    it('getUserStats calls /users/me/stats', () => {
      expect(content).toContain('/users/me/stats');
    });

    it('getAchievements calls /users/me/achievements', () => {
      expect(content).toContain('/users/me/achievements');
    });

    it('getJournal calls /journal with limit and offset params', () => {
      expect(content).toContain('/journal');
      expect(content).toContain('limit');
      expect(content).toContain('offset');
    });

    it('addJournalNote calls POST /journal/{visitId}/note', () => {
      expect(content).toContain('/journal/');
      expect(content).toContain('/note');
    });

    it('getHeatmap calls /explore/heatmap', () => {
      expect(content).toContain('/explore/heatmap');
    });

    it('getCityPassport calls /passports', () => {
      expect(content).toContain('/passports');
    });
  });

  describe('.env.example', () => {
    it('file exists', () => {
      expect(fs.existsSync(path.join(ROOT, '.env.example'))).toBe(true);
    });

    it('contains EXPO_PUBLIC_API_URL', () => {
      const content = fs.readFileSync(
        path.join(ROOT, '.env.example'),
        'utf-8'
      );
      expect(content).toContain('EXPO_PUBLIC_API_URL=http://localhost:8000');
    });
  });
});
