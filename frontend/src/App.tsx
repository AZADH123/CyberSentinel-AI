import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { AlertQueuePage } from './pages/AlertQueuePage';
import { AlertDetailPage } from './pages/AlertDetailPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { ReviewPage } from './pages/ReviewPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'alerts' | 'incidents' | 'detail' | 'review'>('alerts');
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);

  const handleSelectAlert = (alertId: string) => {
    setSelectedAlertId(alertId);
    setActiveTab('detail');
  };

  const handleSelectIncident = (incidentId: string) => {
    setSelectedIncidentId(incidentId);
    setActiveTab('review');
  };

  const handleReviewIncident = (incidentId: string) => {
    setSelectedIncidentId(incidentId);
    setActiveTab('review');
  };

  return (
    <QueryClientProvider client={queryClient}>
      <Layout
        activeTab={activeTab}
        onNavigate={(tab) => {
          setActiveTab(tab);
        }}
      >
        {activeTab === 'alerts' && (
          <AlertQueuePage onSelectAlert={handleSelectAlert} />
        )}

        {activeTab === 'detail' && selectedAlertId && (
          <AlertDetailPage
            alertId={selectedAlertId}
            onBack={() => setActiveTab('alerts')}
            onGoToReview={(incidentId) => {
              setSelectedIncidentId(incidentId);
              setActiveTab('review');
            }}
          />
        )}

        {activeTab === 'incidents' && (
          <IncidentsPage
            onSelectIncident={handleSelectIncident}
            onReviewIncident={handleReviewIncident}
          />
        )}

        {activeTab === 'review' && selectedIncidentId && (
          <ReviewPage
            incidentId={selectedIncidentId}
            onBack={() => setActiveTab('incidents')}
            onSuccess={() => setActiveTab('incidents')}
          />
        )}
      </Layout>
    </QueryClientProvider>
  );
};

export default App;
