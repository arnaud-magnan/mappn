/**
 * Single journal entry card displayed in the visit timeline.
 *
 * Shows place name, formatted visit date, visit duration, and city.
 * If a text note exists on the entry, a truncated preview is shown.
 * If a local photo URI exists in AsyncStorage (keyed by visit_id),
 * a thumbnail is displayed. Tapping the card navigates to the note
 * edit screen at /journal/{visitId}.
 */

import React, { useEffect, useState } from 'react';
import {
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';

import { JournalEntryResponse } from '@/types/api';
import { THEME_COLORS } from '@/constants/colors';
import { Card } from '@/components/ui/Card';

export interface JournalEntryProps {
  entry: JournalEntryResponse;
}

/** AsyncStorage key for a local journal photo URI, keyed by visit_id. */
const photoStorageKey = (visitId: number) => `journal_photo_${visitId}`;

/** Format a duration in seconds to a human-readable string like "1h 23m" or "45m". */
function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds <= 0) return '';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  if (remainingMinutes === 0) return `${hours}h`;
  return `${hours}h ${remainingMinutes}m`;
}

/** Format an ISO date string to a readable display like "Mon, Jan 15, 2024 at 3:42 PM". */
function formatVisitDate(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function JournalEntry({ entry }: JournalEntryProps) {
  const [localPhotoUri, setLocalPhotoUri] = useState<string | null>(null);

  useEffect(() => {
    const loadLocalPhoto = async () => {
      try {
        const uri = await AsyncStorage.getItem(photoStorageKey(entry.visit_id));
        if (uri !== null) {
          setLocalPhotoUri(uri);
        }
      } catch {
        // Silently ignore AsyncStorage read errors
      }
    };
    loadLocalPhoto();
  }, [entry.visit_id]);

  const handlePress = () => {
    router.push(`/journal/${entry.visit_id}` as const as '/');
  };

  const duration = formatDuration(entry.duration_seconds);
  const hasNote = entry.note !== null && entry.note !== '';
  const hasPhoto = localPhotoUri !== null;

  return (
    <Pressable onPress={handlePress} style={({ pressed }) => [pressed && styles.pressed]}>
      <Card style={styles.card}>
        <View style={styles.header}>
          <View style={styles.titleContainer}>
            <Text style={styles.placeName} numberOfLines={1}>
              {entry.place_name}
            </Text>
            {entry.city !== null && entry.city !== '' && (
              <Text style={styles.cityName} numberOfLines={1}>
                {entry.city}
              </Text>
            )}
          </View>
          {hasPhoto && (
            <Image
              source={{ uri: localPhotoUri! }}
              style={styles.thumbnail}
              resizeMode="cover"
            />
          )}
        </View>

        <View style={styles.metaRow}>
          <Text style={styles.metaText}>{formatVisitDate(entry.started_at)}</Text>
          {duration !== '' && (
            <Text style={styles.durationBadge}>{duration}</Text>
          )}
        </View>

        {hasNote && (
          <Text style={styles.notePreview} numberOfLines={2}>
            {entry.note}
          </Text>
        )}
      </Card>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pressed: {
    opacity: 0.8,
  },
  card: {
    marginHorizontal: 16,
    marginVertical: 6,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  titleContainer: {
    flex: 1,
    marginRight: 8,
  },
  placeName: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME_COLORS.text,
  },
  cityName: {
    fontSize: 13,
    color: THEME_COLORS.textSecondary,
    marginTop: 2,
  },
  thumbnail: {
    width: 60,
    height: 60,
    borderRadius: 8,
    backgroundColor: THEME_COLORS.border,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  metaText: {
    fontSize: 12,
    color: THEME_COLORS.textSecondary,
    flex: 1,
  },
  durationBadge: {
    fontSize: 12,
    color: THEME_COLORS.primary,
    fontWeight: '500',
    marginLeft: 8,
  },
  notePreview: {
    fontSize: 13,
    color: THEME_COLORS.textSecondary,
    lineHeight: 18,
    marginTop: 4,
    fontStyle: 'italic',
  },
});
