import { createTheme } from '@mui/material/styles';

// Material Design 3 Color Scheme
const md3Colors = {
  primary: '#006495',
  onPrimary: '#FFFFFF',
  primaryContainer: '#CBE6FF',
  onPrimaryContainer: '#001E30',
  secondary: '#50606E',
  onSecondary: '#FFFFFF',
  secondaryContainer: '#D3E4F5',
  onSecondaryContainer: '#0C1D29',
  tertiary: '#65587B',
  onTertiary: '#FFFFFF',
  tertiaryContainer: '#EBDDFF',
  onTertiaryContainer: '#211634',
  error: '#BA1A1A',
  onError: '#FFFFFF',
  errorContainer: '#FFDAD6',
  onErrorContainer: '#410002',
  background: '#FDFCFF',
  onBackground: '#1A1C1E',
  surface: '#FDFCFF',
  onSurface: '#1A1C1E',
  surfaceVariant: '#DDE3EA',
  onSurfaceVariant: '#41474D',
  outline: '#72787E',
  outlineVariant: '#C1C7CE',
  shadow: '#000000',
  scrim: '#000000',
  inverseSurface: '#2E3133',
  inverseOnSurface: '#F0F0F3',
  inversePrimary: '#8ECDFF',
  surfaceTint: '#006495',
  surfaceContainerHighest: '#E0E2E5',
  surfaceContainerHigh: '#E6E8EB',
  surfaceContainer: '#ECEEF1',
  surfaceContainerLow: '#F2F4F7',
  surfaceContainerLowest: '#FFFFFF',
  surfaceBright: '#FDFCFF',
  surfaceDim: '#DBDDE0',
};

// Status Colors for Tickets
export const statusColors = {
  backlog: { main: '#006495', container: '#CBE6FF', onContainer: '#001E30' },
  in_progress: { main: '#F59E0B', container: '#FEF3C7', onContainer: '#78350F' },
  clarification: { main: '#DC2626', container: '#FEE2E2', onContainer: '#7F1D1D' },
  testing: { main: '#059669', container: '#D1FAE5', onContainer: '#064E3B' },
  done: { main: '#6B7280', container: '#F3F4F6', onContainer: '#1F2937' },
};

// Priority Colors
export const priorityColors = {
  high: { main: '#DC2626', container: '#FEE2E2', onContainer: '#7F1D1D' },
  medium: { main: '#F59E0B', container: '#FEF3C7', onContainer: '#78350F' },
  low: { main: '#059669', container: '#D1FAE5', onContainer: '#064E3B' },
};

// Create Material Design 3 Theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: md3Colors.primary,
      contrastText: md3Colors.onPrimary,
      light: md3Colors.primaryContainer,
      dark: md3Colors.onPrimaryContainer,
    },
    secondary: {
      main: md3Colors.secondary,
      contrastText: md3Colors.onSecondary,
      light: md3Colors.secondaryContainer,
      dark: md3Colors.onSecondaryContainer,
    },
    error: {
      main: md3Colors.error,
      contrastText: md3Colors.onError,
      light: md3Colors.errorContainer,
      dark: md3Colors.onErrorContainer,
    },
    background: {
      default: md3Colors.background,
      paper: md3Colors.surface,
    },
    text: {
      primary: md3Colors.onSurface,
      secondary: md3Colors.onSurfaceVariant,
    },
    divider: md3Colors.outlineVariant,
  },
  typography: {
    fontFamily: 'Roboto, -apple-system, BlinkMacSystemFont, sans-serif',
    // Material Design 3 Type Scale
    displayLarge: {
      fontSize: '3.5625rem',
      fontWeight: 400,
      lineHeight: 1.25,
      letterSpacing: '-0.0156rem',
    },
    displayMedium: {
      fontSize: '2.8125rem',
      fontWeight: 400,
      lineHeight: 1.28,
      letterSpacing: '0',
    },
    displaySmall: {
      fontSize: '2.25rem',
      fontWeight: 400,
      lineHeight: 1.33,
      letterSpacing: '0',
    },
    headlineLarge: {
      fontSize: '2rem',
      fontWeight: 400,
      lineHeight: 1.4,
      letterSpacing: '0',
    },
    headlineMedium: {
      fontSize: '1.75rem',
      fontWeight: 400,
      lineHeight: 1.4,
      letterSpacing: '0',
    },
    headlineSmall: {
      fontSize: '1.5rem',
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0',
    },
    titleLarge: {
      fontSize: '1.375rem',
      fontWeight: 400,
      lineHeight: 1.4,
      letterSpacing: '0',
    },
    titleMedium: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
      letterSpacing: '0.0094rem',
    },
    titleSmall: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.5,
      letterSpacing: '0.0063rem',
    },
    labelLarge: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.5,
      letterSpacing: '0.0063rem',
    },
    labelMedium: {
      fontSize: '0.75rem',
      fontWeight: 500,
      lineHeight: 1.5,
      letterSpacing: '0.0313rem',
    },
    labelSmall: {
      fontSize: '0.6875rem',
      fontWeight: 500,
      lineHeight: 1.5,
      letterSpacing: '0.0313rem',
    },
    bodyLarge: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0.0094rem',
    },
    bodyMedium: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0.0156rem',
    },
    bodySmall: {
      fontSize: '0.75rem',
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0.025rem',
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12, // M3 uses rounded corners
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 1px 3px rgba(0,0,0,0.12), 0px 1px 2px rgba(0,0,0,0.08)',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: '0px 4px 8px rgba(0,0,0,0.12), 0px 2px 4px rgba(0,0,0,0.08)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 20, // M3 buttons are rounded
          textTransform: 'none',
          fontWeight: 500,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 2px 4px rgba(0,0,0,0.12)',
          },
        },
      },
    },
    MuiFab: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0px 4px 8px rgba(0,0,0,0.15), 0px 1px 3px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 28, // M3 dialogs have large rounded corners
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
    MuiListItem: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
        },
      },
    },
  },
});

export default theme;
