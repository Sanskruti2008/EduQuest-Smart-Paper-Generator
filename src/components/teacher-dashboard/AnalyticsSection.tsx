import { Suspense, lazy } from 'react';
import AnalyticsSkeleton from './AnalyticsSkeleton';

const TeacherDashboardAnalytics = lazy(() => import('../TeacherDashboardAnalytics'));

export default function AnalyticsSection() {
  return (
    <Suspense fallback={<AnalyticsSkeleton />}>
      <TeacherDashboardAnalytics />
    </Suspense>
  );
}
