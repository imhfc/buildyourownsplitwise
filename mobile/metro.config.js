const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

// Fix: Expo 55 defaults unstable_enablePackageExports to true, which causes
// Metro to resolve Zustand's ESM (.mjs) files that contain import.meta.env —
// a syntax Metro cannot handle. Setting false forces CJS resolution instead.
config.resolver.unstable_enablePackageExports = false;

module.exports = withNativeWind(config, { input: "./global.css" });
