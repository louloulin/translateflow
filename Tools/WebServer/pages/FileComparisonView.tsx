import React from 'react';
import { FileComparisonDashboard } from '@/components/FileComparisonDashboard';

interface FileComparisonViewProps {
  projectId: string;
}

export const FileComparisonView: React.FC<FileComparisonViewProps> = ({ projectId }) => {
  return <FileComparisonDashboard projectId={projectId} />;
};
