const path = require("path");

/** @type {import('jest').Config} */
module.exports = {
  preset: path.resolve(__dirname, "node_modules/jest-expo"),
  roots: ["<rootDir>/__tests__"],
  transformIgnorePatterns: [
    "node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|native-base|react-native-svg|nativewind|react-native-css-interop|lucide-react-native|clsx|tailwind-merge)",
  ],
  setupFilesAfterSetup: [
    path.resolve(__dirname, "node_modules/@testing-library/react-native/extend-expect"),
  ],
  moduleNameMapper: {
    "^~/(.*)$": "<rootDir>/$1",
  },
  resolver: undefined,
};
