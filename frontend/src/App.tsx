import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import TrendRadar from "./pages/TrendRadar";
import CommentMining from "./pages/CommentMining";
import ViralAnatomy from "./pages/ViralAnatomy";
import VerticalDeep from "./pages/VerticalDeep";
import Reports from "./pages/Reports";
import RawData from "./pages/RawData";
import Settings from "./pages/Settings";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 10000, retry: 1 } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/"               element={<Dashboard />} />
            <Route path="/trend-radar"    element={<TrendRadar />} />
            <Route path="/comment-mining" element={<CommentMining />} />
            <Route path="/viral-anatomy"  element={<ViralAnatomy />} />
            <Route path="/vertical-deep"  element={<VerticalDeep />} />
            <Route path="/reports"        element={<Reports />} />
            <Route path="/reports/:id"    element={<Reports />} />
            <Route path="/raw-data"       element={<RawData />} />
            <Route path="/settings"       element={<Settings />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
