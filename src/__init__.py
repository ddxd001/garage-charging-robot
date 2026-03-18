"""
Garage Charging Robot Simulation Package

A modular simulation framework for omni-directional mobile robot
path tracking control in garage environments with performance evaluation,
parameter comparison experiments, and state machine task flow.
"""

__version__ = "1.3.0"
__author__ = "Garage Robot Team"

from .config import SimulationConfig
from .chassis import OmniDirectionalRobot
from .controller import OmniPathTrackingController
from .path_planner import PathPlanner
from .simulator import Simulator, SimulationData
from .plotting import ResultVisualizer
from .metrics import PerformanceMetrics, MetricsCalculator
from .experiment import ParameterComparisonExperiment, ParameterSet
from .state_machine import ChargingRobotStateMachine, RobotState, StateTransition

__all__ = [
    "SimulationConfig",
    "OmniDirectionalRobot",
    "OmniPathTrackingController",
    "PathPlanner",
    "Simulator",
    "SimulationData",
    "ResultVisualizer",
    "PerformanceMetrics",
    "MetricsCalculator",
    "ParameterComparisonExperiment",
    "ParameterSet",
    "ChargingRobotStateMachine",
    "RobotState",
    "StateTransition",
]
