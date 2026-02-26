/**
 * Auth group stack layout.
 *
 * Provides a simple Stack navigator for the authentication screens
 * (login and register). No tab bar is shown in this group.
 * Headers are hidden since each screen renders its own title.
 */

import { Stack } from 'expo-router';

export default function AuthLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen
        name="login"
        options={{
          title: 'Login',
          headerShown: false,
        }}
      />
      <Stack.Screen
        name="register"
        options={{
          title: 'Register',
          headerShown: false,
        }}
      />
    </Stack>
  );
}
