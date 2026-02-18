import { Amplify } from 'aws-amplify';
import { AppRouter } from './Router';
import { AppProvider } from './context/AppContext';
import { SkipLink } from './components/SkipLink';
import './App.css';
import '@aws-amplify/ui-react/styles.css';

// Configure Amplify
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || '',
      userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || '',
    }
  }
});

function App() {
  return (
    <AppProvider>
      <SkipLink />
      <AppRouter />
    </AppProvider>
  )
}

export default App

