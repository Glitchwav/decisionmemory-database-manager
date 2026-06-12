import useSWR from 'swr';
import { fetchAPI } from './client';
import type {
  OverviewResponse,
  ScorePoint,
  RollingMetricPoint,
  MemoryGrowthPoint,
  OWMScorePoint,
  CalibrationPoint,
  StrategyDetailResponse,
  ReflectionSummary,
  AdjustmentEvent,
  BeliefState,
  DreamSession,
  EvolutionRunResponse,
} from './types';

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

function fetcher<T>(endpoint: string): Promise<T> {
  return fetchAPI<T>(endpoint);
}

type SWRResult<T> = {
  data: T | undefined;
  error: Error | undefined;
  isLoading: boolean;
  mutate: () => void;
};

function useMock<T>(loader: () => Promise<{ default: T }>): SWRResult<T> {
  const { data, error, isLoading, mutate } = useSWR<T>(
    loader.toString(),
    async () => {
      const mod = await loader();
      return mod.default;
    },
    { revalidateOnFocus: false },
  );
  return { data, error, isLoading, mutate: () => { mutate(); } };
}

export function useOverview(): SWRResult<OverviewResponse> {
  if (USE_MOCK) {
    return useMock<OverviewResponse>(() => import('../mock/overview.json'));
  }
  const result = useSWR<OverviewResponse>('/dashboard/overview', fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useScoreCurve(params?: Record<string, string>): SWRResult<ScorePoint[]> {
  if (USE_MOCK) {
    return useMock<ScorePoint[]>(() => import('../mock/score-curve.json'));
  }
  const key = params ? `/dashboard/score-curve?${new URLSearchParams(params)}` : '/dashboard/score-curve';
  const result = useSWR<ScorePoint[]>(key, fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useRollingMetrics(params?: Record<string, string>): SWRResult<RollingMetricPoint[]> {
  if (USE_MOCK) {
    return useMock<RollingMetricPoint[]>(() => import('../mock/rolling-metrics.json'));
  }
  const key = params ? `/dashboard/rolling-metrics?${new URLSearchParams(params)}` : '/dashboard/rolling-metrics';
  const result = useSWR<RollingMetricPoint[]>(key, fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useMemoryGrowth(params?: Record<string, string>): SWRResult<MemoryGrowthPoint[]> {
  if (USE_MOCK) {
    return useMock<MemoryGrowthPoint[]>(() => import('../mock/memory-growth.json'));
  }
  const key = params ? `/dashboard/memory-growth?${new URLSearchParams(params)}` : '/dashboard/memory-growth';
  const result = useSWR<MemoryGrowthPoint[]>(key, fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useOWMScoreTrend(): SWRResult<OWMScorePoint[]> {
  if (USE_MOCK) {
    return useMock<OWMScorePoint[]>(() => import('../mock/owm-score-trend.json'));
  }
  const result = useSWR<OWMScorePoint[]>('/dashboard/owm-score-trend', fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useConfidenceCal(): SWRResult<CalibrationPoint[]> {
  if (USE_MOCK) {
    return useMock<CalibrationPoint[]>(() => import('../mock/confidence-cal.json'));
  }
  const result = useSWR<CalibrationPoint[]>('/dashboard/confidence-cal', fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useStrategy(name: string): SWRResult<StrategyDetailResponse> {
  if (USE_MOCK) {
    const loaders: Record<string, () => Promise<{ default: StrategyDetailResponse }>> = {
      VolBreakout: () => import('../mock/strategy-vb.json'),
      IntradayMomentum: () => import('../mock/strategy-im.json'),
      Pullback: () => import('../mock/strategy-pb.json'),
    };
    const loader = loaders[name];
    if (loader) {
      return useMock<StrategyDetailResponse>(loader);
    }
  }
  const result = useSWR<StrategyDetailResponse>(`/dashboard/strategy/${name}`, fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useReflections(params?: Record<string, string>): SWRResult<ReflectionSummary[]> {
  if (USE_MOCK) {
    return useMock<ReflectionSummary[]>(() => import('../mock/reflections.json'));
  }
  const key = params ? `/dashboard/reflections?${new URLSearchParams(params)}` : '/dashboard/reflections';
  const result = useSWR<ReflectionSummary[]>(key, fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useAdjustments(): SWRResult<AdjustmentEvent[]> {
  if (USE_MOCK) {
    return useMock<AdjustmentEvent[]>(() => import('../mock/adjustments.json'));
  }
  const result = useSWR<AdjustmentEvent[]>('/dashboard/adjustments', fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useBeliefs(): SWRResult<BeliefState[]> {
  if (USE_MOCK) {
    return useMock<BeliefState[]>(() => import('../mock/beliefs.json'));
  }
  const result = useSWR<BeliefState[]>('/dashboard/beliefs', fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useDreamResults(): SWRResult<DreamSession[]> {
  if (USE_MOCK) {
    return useMock<DreamSession[]>(() => import('../mock/dream-results.json'));
  }
  const result = useSWR<DreamSession[]>('/dashboard/dream-results', fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}

export function useEvolution(): SWRResult<EvolutionRunResponse> {
  if (USE_MOCK) {
    return useMock<EvolutionRunResponse>(() => import('../mock/evolution.json'));
  }
  const result = useSWR<EvolutionRunResponse>('/dashboard/evolution', fetcher);
  return { data: result.data, error: result.error, isLoading: result.isLoading, mutate: () => { result.mutate(); } };
}
