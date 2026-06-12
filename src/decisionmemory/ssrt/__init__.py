"""SSRT -- Sequential Strategy Retirement Testing.

Provides statistically rigorous strategy retirement decisions using
mSPRT (Mixture Sequential Probability Ratio Test) with regime-aware
null hypotheses.
"""

from decisionmemory.ssrt.models import DecisionResult, SSRTVerdict, RegimeBaseline, RetirementReport
from decisionmemory.ssrt.core import MixtureSPRT
from decisionmemory.ssrt.regime import RegimeAwareNull
