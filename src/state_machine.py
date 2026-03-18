#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务状态机模块

本模块实现了充电机器人的任务状态机，管理完整的充电流程：
- IDLE：空闲等待
- MOVE_TO_TARGET：路径跟踪移动
- ALIGN_TO_DOCK：精确对准
- DOCKED：对接完成
- FINISHED：任务完成

状态机特点：
    - 简单清晰的状态转换逻辑
    - 详细的状态转换日志
    - 支持不同状态下的速度调节

作者：车库机器人团队
版本：1.3.0
日期：2026-03
"""

from enum import Enum, auto
from typing import Optional, List, Tuple
from dataclasses import dataclass
import time


class RobotState(Enum):
    """
    Robot states for charging task.
    
    State Flow:
    IDLE -> MOVE_TO_TARGET -> ALIGN_TO_DOCK -> DOCKED -> FINISHED
    """
    IDLE = auto()              # Initial state, waiting to start
    MOVE_TO_TARGET = auto()    # Moving along path to charging area
    ALIGN_TO_DOCK = auto()     # Fine alignment for docking
    DOCKED = auto()            # Successfully docked at charging station
    FINISHED = auto()          # Task completed


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: RobotState
    to_state: RobotState
    timestamp: float
    reason: str


class ChargingRobotStateMachine:
    """
    State machine for garage charging robot task flow.
    
    This implements a simple, clear state machine without complex event frameworks.
    Each state has explicit entry/exit conditions.
    
    State Descriptions:
    
    1. IDLE:
       - Entry: Initial state or after reset
       - Exit: Task start command received
       - Action: None
    
    2. MOVE_TO_TARGET:
       - Entry: From IDLE when task starts
       - Exit: Robot reaches near-target zone (within pre-dock distance)
       - Action: Execute path tracking control
    
    3. ALIGN_TO_DOCK:
       - Entry: From MOVE_TO_TARGET when near target
       - Exit: Robot achieves precise alignment (position + heading within tolerance)
       - Action: Low-speed fine positioning and heading correction
    
    4. DOCKED:
       - Entry: From ALIGN_TO_DOCK when aligned
       - Exit: Docking duration completed
       - Action: Simulate charging (wait for duration)
    
    5. FINISHED:
       - Entry: From DOCKED when charging complete
       - Exit: None (terminal state)
       - Action: None
    """
    
    def __init__(
        self,
        pre_dock_distance: float = 0.5,
        dock_position_tolerance: float = 0.05,
        dock_heading_tolerance: float = 5.0,
        docking_duration: float = 2.0
    ):
        """
        Initialize the state machine.
        
        Args:
            pre_dock_distance: Distance to target to trigger alignment (m)
            dock_position_tolerance: Position tolerance for docking (m)
            dock_heading_tolerance: Heading tolerance for docking (degrees)
            docking_duration: Time to stay in DOCKED state (s)
        """
        self.current_state = RobotState.IDLE
        self.previous_state: Optional[RobotState] = None
        
        # State transition parameters
        self.pre_dock_distance = pre_dock_distance
        self.dock_position_tolerance = dock_position_tolerance
        self.dock_heading_tolerance = dock_heading_tolerance
        self.docking_duration = docking_duration
        
        # State history
        self.state_history: List[StateTransition] = []
        self.state_start_time: float = 0.0
        self.docked_start_time: float = 0.0
        
        # Task started flag
        self.task_started = False
    
    def start_task(self, current_time: float) -> None:
        """
        Start the charging task.
        
        Args:
            current_time: Current simulation time (s)
        """
        if self.current_state == RobotState.IDLE:
            self.task_started = True
            self._transition_to(RobotState.MOVE_TO_TARGET, current_time, "Task started")
    
    def update(
        self,
        current_time: float,
        distance_to_goal: float,
        position_error: float,
        heading_error: float
    ) -> RobotState:
        """
        Update state machine based on current conditions.
        
        Args:
            current_time: Current simulation time (s)
            distance_to_goal: Distance to goal position (m)
            position_error: Current position error (m)
            heading_error: Current heading error (degrees)
            
        Returns:
            RobotState: Current state after update
        """
        if self.current_state == RobotState.IDLE:
            # Wait for task start
            pass
        
        elif self.current_state == RobotState.MOVE_TO_TARGET:
            # Check if close enough to start alignment
            if distance_to_goal < self.pre_dock_distance:
                self._transition_to(
                    RobotState.ALIGN_TO_DOCK,
                    current_time,
                    f"Reached pre-dock zone (distance: {distance_to_goal:.3f} m)"
                )
        
        elif self.current_state == RobotState.ALIGN_TO_DOCK:
            # Check if alignment is achieved
            if (position_error < self.dock_position_tolerance and
                abs(heading_error) < self.dock_heading_tolerance):
                self._transition_to(
                    RobotState.DOCKED,
                    current_time,
                    f"Alignment achieved (pos: {position_error:.4f} m, heading: {heading_error:.2f}°)"
                )
                self.docked_start_time = current_time
        
        elif self.current_state == RobotState.DOCKED:
            # Check if docking duration completed
            if current_time - self.docked_start_time >= self.docking_duration:
                self._transition_to(
                    RobotState.FINISHED,
                    current_time,
                    f"Docking completed ({self.docking_duration:.1f} s)"
                )
        
        elif self.current_state == RobotState.FINISHED:
            # Terminal state
            pass
        
        return self.current_state
    
    def _transition_to(self, new_state: RobotState, timestamp: float, reason: str) -> None:
        """
        Transition to a new state.
        
        Args:
            new_state: Target state
            timestamp: Time of transition
            reason: Reason for transition
        """
        if new_state != self.current_state:
            transition = StateTransition(
                from_state=self.current_state,
                to_state=new_state,
                timestamp=timestamp,
                reason=reason
            )
            self.state_history.append(transition)
            
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_start_time = timestamp
    
    def get_state_name(self) -> str:
        """Get current state name as string."""
        return self.current_state.name
    
    def get_control_mode(self) -> str:
        """
        Get the control mode for current state.
        
        Returns:
            str: Control mode ('normal', 'precision', 'hold', 'idle')
        """
        if self.current_state == RobotState.IDLE:
            return 'idle'
        elif self.current_state == RobotState.MOVE_TO_TARGET:
            return 'normal'
        elif self.current_state == RobotState.ALIGN_TO_DOCK:
            return 'precision'
        elif self.current_state in [RobotState.DOCKED, RobotState.FINISHED]:
            return 'hold'
        return 'idle'
    
    def get_max_velocity_scale(self) -> float:
        """
        Get velocity scaling factor for current state.
        
        Returns:
            float: Velocity scale (0.0 to 1.0)
        """
        if self.current_state == RobotState.IDLE:
            return 0.0
        elif self.current_state == RobotState.MOVE_TO_TARGET:
            return 1.0  # Full speed
        elif self.current_state == RobotState.ALIGN_TO_DOCK:
            return 0.3  # 30% speed for precision
        elif self.current_state in [RobotState.DOCKED, RobotState.FINISHED]:
            return 0.0  # Stop
        return 0.0
    
    def is_task_complete(self) -> bool:
        """Check if task is complete."""
        return self.current_state == RobotState.FINISHED
    
    def print_state_log(self) -> None:
        """Print state transition log."""
        print("\n" + "=" * 70)
        print("STATE TRANSITION LOG")
        print("=" * 70)
        
        if not self.state_history:
            print("No state transitions recorded.")
            return
        
        print(f"{'Time (s)':<10} {'From State':<20} {'To State':<20} {'Reason':<30}")
        print("-" * 70)
        
        for transition in self.state_history:
            print(f"{transition.timestamp:<10.2f} "
                  f"{transition.from_state.name:<20} "
                  f"{transition.to_state.name:<20} "
                  f"{transition.reason:<30}")
        
        print("=" * 70)
        print(f"Final State: {self.current_state.name}")
        print(f"Total Transitions: {len(self.state_history)}")
        print("=" * 70)
    
    def get_state_durations(self) -> dict:
        """
        Calculate time spent in each state.
        
        Returns:
            dict: State name -> duration (s)
        """
        durations = {state.name: 0.0 for state in RobotState}
        
        for i, transition in enumerate(self.state_history):
            if i < len(self.state_history) - 1:
                duration = self.state_history[i + 1].timestamp - transition.timestamp
                durations[transition.to_state.name] += duration
            else:
                # Last state (current state) - use current time if available
                # This will be updated by the caller if needed
                pass
        
        return durations
    
    def reset(self) -> None:
        """Reset state machine to initial state."""
        self.current_state = RobotState.IDLE
        self.previous_state = None
        self.state_history = []
        self.state_start_time = 0.0
        self.docked_start_time = 0.0
        self.task_started = False
