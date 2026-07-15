import { BrowserRouter, Route, Routes } from "react-router-dom";

import CreateJobPage from "@/pages/CreateJobPage";
import JobMonitorPage from "@/pages/JobMonitorPage";
import ResultsPage from "@/pages/ResultsPage";

export default function App() {
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
