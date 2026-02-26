/**
 * Achievement definitions for the Mappn utility app.
 *
 * These 6 achievements span 3 categories:
 * - Explorer: Wanderer, Globe Trotter
 * - Habits: Night Owl, Early Bird
 * - Categories: Foodie, Culture Vulture
 *
 * Each definition includes the id, display name, description, category,
 * and threshold count required to unlock the achievement.
 */

export interface AchievementDefinition {
  id: string;
  name: string;
  description: string;
  category: 'explorer' | 'habits' | 'categories';
  threshold: number;
  icon: string;
}

export const ACHIEVEMENT_DEFINITIONS: readonly AchievementDefinition[] = [
  {
    id: 'wanderer',
    name: 'Wanderer',
    description: 'Visit 10 distinct neighborhoods',
    category: 'explorer',
    threshold: 10,
    icon: 'explore',
  },
  {
    id: 'globe_trotter',
    name: 'Globe Trotter',
    description: 'Visit 5 distinct cities',
    category: 'explorer',
    threshold: 5,
    icon: 'flight',
  },
  {
    id: 'night_owl',
    name: 'Night Owl',
    description: 'Visit 10 places after midnight',
    category: 'habits',
    threshold: 10,
    icon: 'nightlight-round',
  },
  {
    id: 'early_bird',
    name: 'Early Bird',
    description: 'Visit 10 places before 7am',
    category: 'habits',
    threshold: 10,
    icon: 'wb-sunny',
  },
  {
    id: 'foodie',
    name: 'Foodie',
    description: 'Visit 50 restaurants',
    category: 'categories',
    threshold: 50,
    icon: 'restaurant',
  },
  {
    id: 'culture_vulture',
    name: 'Culture Vulture',
    description: 'Visit 20 museums',
    category: 'categories',
    threshold: 20,
    icon: 'museum',
  },
] as const;

/** Achievement categories for grouping in the UI. */
export const ACHIEVEMENT_CATEGORIES = [
  { key: 'explorer', label: 'Explorer' },
  { key: 'habits', label: 'Habits' },
  { key: 'categories', label: 'Categories' },
] as const;
