import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..');

describe('Step 10 Fix: Place Detail Visit History Integration', () => {
  // =========================================================================
  // 1. useVisitHistory hook
  // =========================================================================
  describe('hooks/useVisitHistory.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'hooks/useVisitHistory.ts');

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

    it('imports getVisitHistory from visitsService', () => {
      expect(content).toContain('getVisitHistory');
      expect(content).toContain('visitsService');
    });

    it('imports VisitResponse type', () => {
      expect(content).toContain('VisitResponse');
    });

    it('exports useVisitHistory hook', () => {
      expect(content).toMatch(
        /export\s+(const|function)\s+useVisitHistory/
      );
    });

    it('uses queryKey with visits and history', () => {
      expect(content).toContain("'visits'");
      expect(content).toContain("'history'");
    });

    it('sets staleTime using STALE_TIME constant', () => {
      expect(content).toMatch(/STALE_TIME\.VISITS|300000|5\s*\*\s*60\s*\*\s*1000/);
    });

    it('calls getVisitHistory in queryFn', () => {
      expect(content).toMatch(/getVisitHistory/);
    });
  });

  // =========================================================================
  // 2. STALE_TIME.VISITS constant
  // =========================================================================
  describe('constants/config.ts', () => {
    let content: string;
    const filePath = path.join(ROOT, 'constants/config.ts');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('has VISITS stale time constant', () => {
      expect(content).toMatch(/VISITS/);
    });

    it('VISITS stale time is 5 minutes (300000ms)', () => {
      expect(content).toMatch(/VISITS:\s*5\s*\*\s*60\s*\*\s*1000/);
    });
  });

  // =========================================================================
  // 3. Place Detail Screen uses visit history data
  // =========================================================================
  describe('app/place/[id].tsx visit history integration', () => {
    let content: string;
    const filePath = path.join(ROOT, 'app/place/[id].tsx');

    beforeAll(() => {
      content = fs.readFileSync(filePath, 'utf-8');
    });

    it('imports useVisitHistory hook', () => {
      expect(content).toContain('useVisitHistory');
    });

    it('does NOT hardcode visits to an empty array', () => {
      // The old implementation had: const visits = useMemo<VisitResponse[]>(() => [], []);
      expect(content).not.toMatch(
        /const\s+visits\s*=\s*useMemo<VisitResponse\[\]>\(\(\)\s*=>\s*\[\],\s*\[\]\)/
      );
    });

    it('filters visits by place_id', () => {
      expect(content).toMatch(/place_id/);
      expect(content).toMatch(/filter/);
    });

    it('passes filtered visits to VisitHistoryList', () => {
      expect(content).toContain('VisitHistoryList');
      expect(content).toMatch(/visits=/);
    });

    it('calls useVisitHistory hook', () => {
      expect(content).toMatch(/useVisitHistory\(\)/);
    });
  });
});
