/**
 * Internationalization (i18n) Infrastructure
 * Lightweight translation system for MediBot UI strings.
 * Supports English, Telugu, Hindi, Spanish.
 */

// ---- Supported Locales ----
export type Locale = 'en' | 'te' | 'hi' | 'es';

export const LOCALE_LABELS: Record<Locale, string> = {
    en: 'English',
    te: 'తెలుగు',
    hi: 'हिन्दी',
    es: 'Español',
};

// ---- Translation Keys ----
export interface Translations {
    // Navigation
    'nav.chat': string;
    'nav.history': string;
    'nav.profile': string;
    'nav.upload': string;
    'nav.newChat': string;
    'nav.signIn': string;
    'nav.signOut': string;

    // Chat
    'chat.placeholder': string;
    'chat.send': string;
    'chat.generating': string;
    'chat.error': string;
    'chat.tryAgain': string;
    'chat.guestLimit': string;

    // History  
    'history.title': string;
    'history.search': string;
    'history.empty': string;
    'history.export': string;

    // Profile
    'profile.title': string;
    'profile.conditions': string;
    'profile.medications': string;
    'profile.allergies': string;

    // General
    'loading': string;
    'error.generic': string;
    'error.network': string;
}

// ---- English (default) ----
const en: Translations = {
    'nav.chat': 'Chat',
    'nav.history': 'History',
    'nav.profile': 'Profile',
    'nav.upload': 'Upload Report',
    'nav.newChat': 'New Chat',
    'nav.signIn': 'Sign In / Sign Up',
    'nav.signOut': 'Sign Out',

    'chat.placeholder': 'Describe your medical question...',
    'chat.send': 'Send',
    'chat.generating': 'Generating response...',
    'chat.error': 'Something went wrong. Please try again.',
    'chat.tryAgain': 'Try Again',
    'chat.guestLimit': 'Guest message limit reached. Please sign in to continue.',

    'history.title': 'Chat History',
    'history.search': 'Search conversations...',
    'history.empty': 'No conversations yet.',
    'history.export': 'Export as PDF',

    'profile.title': 'Health Profile',
    'profile.conditions': 'Conditions',
    'profile.medications': 'Medications',
    'profile.allergies': 'Allergies',

    'loading': 'Loading...',
    'error.generic': 'Something went wrong.',
    'error.network': 'Network error. Please check your connection.',
};

// ---- Telugu ----
const te: Translations = {
    'nav.chat': 'చాట్',
    'nav.history': 'చరిత్ర',
    'nav.profile': 'ప్రొఫైల్',
    'nav.upload': 'రిపోర్ట్ అప్‌లోడ్',
    'nav.newChat': 'కొత్త చాట్',
    'nav.signIn': 'సైన్ ఇన్ / సైన్ అప్',
    'nav.signOut': 'సైన్ అవుట్',

    'chat.placeholder': 'మీ వైద్య ప్రశ్నను వివరించండి...',
    'chat.send': 'పంపు',
    'chat.generating': 'ప్రతిస్పందన రూపొందిస్తోంది...',
    'chat.error': 'ఏదో తప్పు జరిగింది. దయచేసి మళ్ళీ ప్రయత్నించండి.',
    'chat.tryAgain': 'మళ్ళీ ప్రయత్నించు',
    'chat.guestLimit': 'అతిథి సందేశ పరిమితి చేరుకుంది. కొనసాగించడానికి సైన్ ఇన్ చేయండి.',

    'history.title': 'చాట్ చరిత్ర',
    'history.search': 'సంభాషణలు శోధించండి...',
    'history.empty': 'ఇంకా సంభాషణలు లేవు.',
    'history.export': 'PDFగా ఎగుమతి',

    'profile.title': 'ఆరోగ్య ప్రొఫైల్',
    'profile.conditions': 'వ్యాధులు',
    'profile.medications': 'మందులు',
    'profile.allergies': 'అలర్జీలు',

    'loading': 'లోడ్ అవుతోంది...',
    'error.generic': 'ఏదో తప్పు జరిగింది.',
    'error.network': 'నెట్‌వర్క్ లోపం. మీ కనెక్షన్‌ను తనిఖీ చేయండి.',
};

// ---- Hindi ----
const hi: Translations = {
    'nav.chat': 'चैट',
    'nav.history': 'इतिहास',
    'nav.profile': 'प्रोफ़ाइल',
    'nav.upload': 'रिपोर्ट अपलोड',
    'nav.newChat': 'नई चैट',
    'nav.signIn': 'साइन इन / साइन अप',
    'nav.signOut': 'साइन आउट',

    'chat.placeholder': 'अपना चिकित्सा प्रश्न बताएं...',
    'chat.send': 'भेजें',
    'chat.generating': 'प्रतिक्रिया तैयार हो रही है...',
    'chat.error': 'कुछ गलत हो गया। कृपया पुनः प्रयास करें।',
    'chat.tryAgain': 'पुनः प्रयास',
    'chat.guestLimit': 'अतिथि संदेश सीमा पूरी हो गई। जारी रखने के लिए साइन इन करें।',

    'history.title': 'चैट इतिहास',
    'history.search': 'बातचीत खोजें...',
    'history.empty': 'अभी तक कोई बातचीत नहीं।',
    'history.export': 'PDF के रूप में निर्यात',

    'profile.title': 'स्वास्थ्य प्रोफ़ाइल',
    'profile.conditions': 'रोग',
    'profile.medications': 'दवाइयाँ',
    'profile.allergies': 'एलर्जी',

    'loading': 'लोड हो रहा है...',
    'error.generic': 'कुछ गलत हो गया।',
    'error.network': 'नेटवर्क त्रुटि। कृपया अपना कनेक्शन जांचें।',
};

// ---- Spanish ----
const es: Translations = {
    'nav.chat': 'Chat',
    'nav.history': 'Historial',
    'nav.profile': 'Perfil',
    'nav.upload': 'Subir Informe',
    'nav.newChat': 'Nuevo Chat',
    'nav.signIn': 'Iniciar Sesión / Registrarse',
    'nav.signOut': 'Cerrar Sesión',

    'chat.placeholder': 'Describe tu pregunta médica...',
    'chat.send': 'Enviar',
    'chat.generating': 'Generando respuesta...',
    'chat.error': 'Algo salió mal. Por favor, inténtalo de nuevo.',
    'chat.tryAgain': 'Reintentar',
    'chat.guestLimit': 'Límite de mensajes de invitado alcanzado. Inicia sesión para continuar.',

    'history.title': 'Historial de Chat',
    'history.search': 'Buscar conversaciones...',
    'history.empty': 'Aún no hay conversaciones.',
    'history.export': 'Exportar como PDF',

    'profile.title': 'Perfil de Salud',
    'profile.conditions': 'Condiciones',
    'profile.medications': 'Medicamentos',
    'profile.allergies': 'Alergias',

    'loading': 'Cargando...',
    'error.generic': 'Algo salió mal.',
    'error.network': 'Error de red. Verifica tu conexión.',
};

// ---- Translation Map ----
const translations: Record<Locale, Translations> = { en, te, hi, es };

/**
 * Get a translated string for the given key and locale.
 * Falls back to English if the key is not found in the target locale.
 */
export function t(key: keyof Translations, locale: Locale = 'en'): string {
    return translations[locale]?.[key] ?? translations.en[key] ?? key;
}

/**
 * Create a bound translator for a specific locale.
 * Usage: const t = createTranslator('te'); t('nav.chat') // 'చాట్'
 */
export function createTranslator(locale: Locale) {
    return (key: keyof Translations) => t(key, locale);
}
