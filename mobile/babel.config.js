module.exports = function (api) {
  api.cache(true);

  const isTest = process.env.NODE_ENV === "test";

  if (isTest) {
    return {
      presets: [require.resolve("babel-preset-expo")],
    };
  }

  return {
    presets: [
      [require.resolve("babel-preset-expo"), { jsxImportSource: "nativewind" }],
      require.resolve("nativewind/babel"),
    ],
    plugins: [require.resolve("react-native-reanimated/plugin")],
  };
};
