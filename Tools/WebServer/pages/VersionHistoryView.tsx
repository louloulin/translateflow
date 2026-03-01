import React from 'react';
import { VersionHistoryViewer } from '@/components/VersionHistoryViewer';

export function VersionHistoryView() {
  // Get projectId and fileId from URL hash: #/history/projectId/fileId
  const hash = window.location.hash;
  const parts = hash.split('/').filter(Boolean);

  // parts[0] = 'history', parts[1] = projectId, parts[2] = fileId
  const projectId = parts[1] || '';
  const fileId = parts[2] || '';

  const handleBack = () => {
    window.location.hash = `/editor/${projectId}/${fileId}`;
  };

  if (!projectId || !fileId) {
    return (
      <div className="flex items-center justify-center h-full">
        <p>Invalid project or file ID</p>
      </div>
    );
  }

  return (
    <VersionHistoryViewer
      projectId={projectId}
      fileId={fileId}
      fileName={`File ${fileId}`}
      onBack={handleBack}
    />
  );
}
