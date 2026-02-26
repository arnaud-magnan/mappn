/**
 * Journal note edit screen – add or update a text note and optional photo
 * for a specific visit.
 *
 * Text notes (max 1000 chars) are saved to the backend via
 * utilityService.addJournalNote(visitId, text, photoUrl).
 * Photos are stored on-device only: the picked image URI is saved to
 * AsyncStorage keyed by the visit_id so it persists across app launches.
 *
 * Navigation: Reached via router.push('/journal/{visitId}') from JournalEntry.
 * Back navigation uses router.back().
 */

import React, { useEffect, useState } from 'react';
import {
  Alert,
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import { router, useLocalSearchParams } from 'expo-router';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

import { addJournalNote } from '@/services/utilityService';
import { THEME_COLORS } from '@/constants/colors';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const NOTE_MAX_LENGTH = 1000;

/** AsyncStorage key for a local journal photo URI, keyed by visit_id. */
const photoStorageKey = (visitId: string) => `journal_photo_${visitId}`;

export default function JournalNoteEditScreen() {
  const { visitId } = useLocalSearchParams<{ visitId: string }>();

  const [noteText, setNoteText] = useState('');
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingInitial, setIsLoadingInitial] = useState(true);

  // Load existing note text and local photo from AsyncStorage on mount.
  // The text note from the backend is not pre-loaded here since it would
  // require an additional API call; the user starts fresh or edits inline.
  useEffect(() => {
    if (visitId === undefined) return;

    const loadLocalPhoto = async () => {
      try {
        const uri = await AsyncStorage.getItem(photoStorageKey(visitId));
        if (uri !== null) {
          setPhotoUri(uri);
        }
      } catch {
        // Ignore AsyncStorage read errors
      } finally {
        setIsLoadingInitial(false);
      }
    };

    loadLocalPhoto();
  }, [visitId]);

  const handlePickPhoto = async () => {
    const permissionResult =
      await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permissionResult.granted) {
      Alert.alert(
        'Permission Required',
        'Please grant photo library access to add photos to your journal.'
      );
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
      aspect: [4, 3],
    });

    if (!result.canceled && result.assets.length > 0) {
      setPhotoUri(result.assets[0].uri);
    }
  };

  const handleRemovePhoto = () => {
    setPhotoUri(null);
  };

  const handleSave = async () => {
    if (visitId === undefined) return;

    setIsSaving(true);
    try {
      // Save text note to backend
      await addJournalNote(
        Number(visitId),
        noteText,
        // Photo URL not sent to backend (on-device only per architecture decision)
        undefined
      );

      // Save local photo URI to AsyncStorage
      if (photoUri !== null) {
        await AsyncStorage.setItem(photoStorageKey(visitId), photoUri);
      } else {
        await AsyncStorage.removeItem(photoStorageKey(visitId));
      }

      router.back();
    } catch {
      Alert.alert(
        'Save Failed',
        'Could not save your note. Please check your connection and try again.'
      );
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoadingInitial) {
    return <LoadingSpinner />;
  }

  const charCount = noteText.length;
  const isOverLimit = charCount > NOTE_MAX_LENGTH;

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={styles.header}>
        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
          hitSlop={8}>
          <MaterialIcons name="arrow-back" size={24} color={THEME_COLORS.text} />
        </Pressable>
        <Text style={styles.headerTitle}>Edit Journal Note</Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView
        style={styles.flex}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled">

        {/* Text Note Section */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>Note</Text>
          <TextInput
            style={[styles.noteInput, isOverLimit && styles.noteInputError]}
            value={noteText}
            onChangeText={setNoteText}
            placeholder="Write about your visit..."
            placeholderTextColor={THEME_COLORS.textSecondary}
            multiline
            textAlignVertical="top"
            maxLength={NOTE_MAX_LENGTH}
            accessibilityLabel="Journal note text input"
          />
          <Text
            style={[
              styles.charCounter,
              isOverLimit && styles.charCounterError,
            ]}>
            {charCount}/{NOTE_MAX_LENGTH}
          </Text>
        </View>

        {/* Photo Section */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>Photo</Text>

          {photoUri !== null ? (
            <View style={styles.photoContainer}>
              <Image
                source={{ uri: photoUri }}
                style={styles.photoPreview}
                resizeMode="cover"
              />
              <Pressable
                onPress={handleRemovePhoto}
                style={styles.removePhotoButton}
                hitSlop={8}>
                <MaterialIcons
                  name="close"
                  size={20}
                  color={THEME_COLORS.background}
                />
              </Pressable>
            </View>
          ) : (
            <Button
              title="Pick Photo from Gallery"
              onPress={handlePickPhoto}
              variant="secondary"
            />
          )}
        </View>

        {/* Save Button */}
        <View style={styles.saveContainer}>
          <Button
            title="Save Note"
            onPress={handleSave}
            loading={isSaving}
            disabled={isOverLimit}
            variant="primary"
          />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: THEME_COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: Platform.OS === 'ios' ? 56 : 16,
    paddingBottom: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: THEME_COLORS.border,
    backgroundColor: THEME_COLORS.background,
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: THEME_COLORS.text,
    textAlign: 'center',
  },
  headerSpacer: {
    width: 32,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  section: {
    marginBottom: 24,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: THEME_COLORS.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  noteInput: {
    borderWidth: 1,
    borderColor: THEME_COLORS.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    color: THEME_COLORS.text,
    minHeight: 140,
    backgroundColor: THEME_COLORS.surface,
  },
  noteInputError: {
    borderColor: THEME_COLORS.error,
  },
  charCounter: {
    fontSize: 12,
    color: THEME_COLORS.textSecondary,
    textAlign: 'right',
    marginTop: 4,
  },
  charCounterError: {
    color: THEME_COLORS.error,
  },
  photoContainer: {
    position: 'relative',
    alignSelf: 'flex-start',
  },
  photoPreview: {
    width: 200,
    height: 150,
    borderRadius: 8,
    backgroundColor: THEME_COLORS.border,
  },
  removePhotoButton: {
    position: 'absolute',
    top: 6,
    right: 6,
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderRadius: 12,
    padding: 4,
  },
  saveContainer: {
    marginTop: 8,
  },
});
