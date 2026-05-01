(function () {
  function getStorageArea(name) {
    try {
      return window[name] || null;
    } catch {
      return null;
    }
  }

  function readJson(areaName, key, fallback = null) {
    try {
      const rawValue = getStorageArea(areaName)?.getItem(key);
      return rawValue ? JSON.parse(rawValue) : fallback;
    } catch {
      return fallback;
    }
  }

  function writeJson(areaName, key, value) {
    try {
      getStorageArea(areaName)?.setItem(key, JSON.stringify(value));
    } catch {
      return false;
    }

    return true;
  }

  function readMap(areaName, key) {
    const value = readJson(areaName, key, {});
    return value && typeof value === "object" && !Array.isArray(value)
      ? value
      : {};
  }

  window.PiggyStorage = {
    readJson,
    writeJson,
    readLocalMap(key) {
      return readMap("localStorage", key);
    },
    writeLocalMap(key, value) {
      return writeJson("localStorage", key, value);
    },
    readSessionValue(key) {
      return readJson("sessionStorage", key, null);
    },
    writeSessionValue(key, value) {
      return writeJson("sessionStorage", key, value);
    },
  };
})();
