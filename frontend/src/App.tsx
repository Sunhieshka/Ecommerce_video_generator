import { BrowserRouter, Route, Routes } from "react-router-dom";

import CredentialsPage from "@/pages/CredentialsPage";
import CreateJobPage from "@/pages/CreateJobPage";
import JobMonitorPage from "@/pages/JobMonitorPage";
import ResultsPage from "@/pages/ResultsPage";
import { useCredentials } from "@/store/useCredentials";

export default function App() {
  const credentials = useCredentials((s) => s.credentials);

  if (!credentials) {
    return <CredentialsPage />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CreateJobPage />} />
        <Route path="/jobs/new" element={<CreateJobPage />} />
        <Route path="/jobs/:jobId" element={<JobMonitorPage />} />
        <Route path="/jobs/:jobId/results" element={<ResultsPage />} />
      </Routes>
    </BrowserRouter>
  );
}
