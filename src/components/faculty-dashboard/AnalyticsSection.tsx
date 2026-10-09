import { Suspense, lazy } from 'react';
import AnalyticsSkeleton from './AnalyticsSkeleton';

const FacultyDashboardAnalytics = lazy(() => import('../FacultyDashboardAnalytics'));

export default function AnalyticsSection() {
  return (
    <Suspense fallback={<AnalyticsSkeleton />}>
      <FacultyDashboardAnalytics />
    </Suspense>
  );
}
