document.addEventListener("DOMContentLoaded", () => {
  const preferencesApi = window.PiggyPreferences;
  if (!preferencesApi) return;

  const settingsPageApi =
    window.PiggySettingsPage?.initialize(preferencesApi) || null;

  window.PiggyReaderRuntime?.initialize(preferencesApi, {
    settingsPageApi,
  });
});
