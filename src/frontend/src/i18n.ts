import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import ko from "./locales/ko.json";

const SUPPORTED_LANGUAGE_IDS = ["en", "ko"] as const;
type SupportedLanguageId = (typeof SUPPORTED_LANGUAGE_IDS)[number];
const LANGUAGE_STORAGE_KEY = "b4a_language";

function normalizeLanguageId(value: string | null | undefined): SupportedLanguageId | null {
    if (!value) {
        return null;
    }
    const normalized = value.split("-")[0]?.toLowerCase();
    if (normalized === "en" || normalized === "ko") {
        return normalized;
    }
    return null;
}

function resolveInitialLanguage(): SupportedLanguageId {
    if (typeof window !== "undefined") {
        const stored = normalizeLanguageId(window.localStorage.getItem(LANGUAGE_STORAGE_KEY));
        if (stored) {
            return stored;
        }
        const browserFromList =
            window.navigator.languages
                ?.map((value) => normalizeLanguageId(value))
                .find((value): value is SupportedLanguageId => value !== null) ?? null;
        if (browserFromList) {
            return browserFromList;
        }
        const browser = normalizeLanguageId(window.navigator.language);
        if (browser) {
            return browser;
        }
    }
    return "en";
}

void i18n.use(initReactI18next).init({
    resources: {
        en: {
            translation: en,
        },
        ko: {
            translation: ko,
        },
    },
    lng: resolveInitialLanguage(),
    fallbackLng: "en",
    interpolation: {
        escapeValue: false,
    },
});

i18n.on("languageChanged", (nextLanguage) => {
    if (typeof window === "undefined") {
        return;
    }
    const normalized = normalizeLanguageId(nextLanguage);
    if (!normalized) {
        return;
    }
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, normalized);
});

export default i18n;
