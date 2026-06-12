import type { ScorePoint } from '../../api/types';
import ScoreCurveChartWeb from './ScoreCurveChart.web';

export interface ScoreCurveChartProps {
  data: ScorePoint[];
}

/**
 * Transform raw score points into chart-ready format.
 * Business logic only — no chart library imports.
 */
function transformData(data: ScorePoint[]) {
  return data.map((p) => ({
    time: p.date,
    value: p.cumulative_pnl,
    drawdown: p.drawdown_pct,
    decisions: p.decision_count,
  }));
}

export default function ScoreCurveChart({ data }: ScoreCurveChartProps) {
  const chartData = transformData(data);
  return <ScoreCurveChartWeb data={chartData} />;
}
