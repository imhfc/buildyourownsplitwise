import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./en.json";
import ja from "./ja.json";
import zhTW from "./zh-TW.json";

i18n.use(initReactI18next).init({
  resources: {
    "zh-TW": { translation: zhTW },
    en: { translation: en },
    ja: { translation: ja },
  },
  lng: "zh-TW",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;
