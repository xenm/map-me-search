"""
Custom Observability Plugin for Metrics Tracking (Day 4a)

This plugin tracks key metrics about agent performance:
- Agent invocation count
- Tool usage count
- LLM request count
- Response times
- Token usage
"""

import logging
import time
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from typing import Dict, Any


class MetricsTrackingPlugin(BasePlugin):
    """
    Custom plugin that tracks comprehensive metrics for agent performance analysis.
    
    Features:
    - Counts agent invocations
    - Tracks tool usage
    - Monitors LLM requests
    - Measures response times
    - Accumulates token usage
    """
    
    def __init__(self) -> None:
        """Initialize the plugin with metric counters."""
        super().__init__(name="metrics_tracking")
        
        # Counters
        self.agent_count: int = 0
        self.tool_count: int = 0
        self.llm_request_count: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        
        # Timing
        self.agent_start_times: Dict[str, float] = {}
        self.llm_start_times: Dict[str, float] = {}
        
        # Tool usage tracking
        self.tool_usage: Dict[str, int] = {}
        
        logging.info("[MetricsPlugin] Initialized")
    
    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        """Track when an agent starts."""
        self.agent_count += 1
        agent_id = f"{agent.name}_{self.agent_count}"
        self.agent_start_times[agent_id] = time.time()
        
        logging.info(
            f"[MetricsPlugin] 🤖 Agent started: {agent.name} "
            f"(Total invocations: {self.agent_count})"
        )
    
    async def after_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        """Track when an agent completes."""
        agent_id = f"{agent.name}_{self.agent_count}"
        
        if agent_id in self.agent_start_times:
            duration = time.time() - self.agent_start_times[agent_id]
            logging.info(
                f"[MetricsPlugin] ✅ Agent completed: {agent.name} "
                f"(Duration: {duration:.2f}s)"
            )
            del self.agent_start_times[agent_id]
    
    async def before_model_callback(
        self, *, callback_context: CallbackContext = None, llm_request: Any = None, **kwargs
    ) -> None:
        """Track LLM request initiation."""
        self.llm_request_count += 1
        request_id = f"llm_{self.llm_request_count}"
        self.llm_start_times[request_id] = time.time()
        
        logging.info(
            f"[MetricsPlugin] 🧠 LLM request #{self.llm_request_count} started"
        )
    
    async def after_model_callback(
        self, 
        *, 
        callback_context: CallbackContext = None,
        llm_request: Any = None,
        llm_response: Any = None,
        model_response_event: Any = None,
        **kwargs
    ) -> None:
        """Track LLM response and token usage."""
        request_id = f"llm_{self.llm_request_count}"
        
        if request_id in self.llm_start_times:
            duration = time.time() - self.llm_start_times[request_id]
            del self.llm_start_times[request_id]
        else:
            duration = 0
        
        # Track token usage if available
        if llm_response and hasattr(llm_response, 'usage_metadata'):
            usage_metadata = getattr(llm_response, 'usage_metadata', None)
            if usage_metadata:
                input_tokens_raw = getattr(usage_metadata, 'prompt_token_count', 0)
                output_tokens_raw = getattr(usage_metadata, 'candidates_token_count', 0)

                # Handle None or non-int values defensively
                input_tokens = int(input_tokens_raw or 0)
                output_tokens = int(output_tokens_raw or 0)
                
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                
                logging.info(
                    f"[MetricsPlugin] 🧠 LLM response received "
                    f"(Duration: {duration:.2f}s, Input tokens: {input_tokens}, "
                    f"Output tokens: {output_tokens})"
                )
            else:
                logging.info(
                    f"[MetricsPlugin] 🧠 LLM response received (Duration: {duration:.2f}s)"
                )
        else:
            logging.info(
                f"[MetricsPlugin] 🧠 LLM response received (Duration: {duration:.2f}s)"
            )
    
    async def before_tool_callback(
        self, *, callback_context: CallbackContext = None, tool_name: str = None, tool_input: Any = None, **kwargs
    ) -> None:
        """Track tool usage."""
        if tool_name:
            self.tool_count += 1
            
            # Count individual tool usage
            if tool_name not in self.tool_usage:
                self.tool_usage[tool_name] = 0
            self.tool_usage[tool_name] += 1
            
            logging.info(
                f"[MetricsPlugin] 🔧 Tool called: {tool_name} "
                f"(Total tool calls: {self.tool_count})"
            )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            "agent_invocations": self.agent_count,
            "total_tool_calls": self.tool_count,
            "llm_requests": self.llm_request_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "tool_usage_breakdown": dict(self.tool_usage),
        }
    
    def log_metrics_summary(self) -> None:
        """Log comprehensive metrics summary."""
        metrics = self.get_metrics_summary()
        
        logging.info("\n" + "=" * 60)
        logging.info("📊 METRICS SUMMARY")
        logging.info("=" * 60)
        logging.info(f"🤖 Agent Invocations: {metrics['agent_invocations']}")
        logging.info(f"🔧 Total Tool Calls: {metrics['total_tool_calls']}")
        logging.info(f"🧠 LLM Requests: {metrics['llm_requests']}")
        logging.info(f"🎯 Total Tokens: {metrics['total_tokens']} "
                    f"(Input: {metrics['total_input_tokens']}, "
                    f"Output: {metrics['total_output_tokens']})")
        
        if metrics['tool_usage_breakdown']:
            logging.info("\n📋 Tool Usage Breakdown:")
            for tool, count in sorted(
                metrics['tool_usage_breakdown'].items(), 
                key=lambda x: x[1], 
                reverse=True
            ):
                logging.info(f"   • {tool}: {count} calls")
        
        logging.info("=" * 60 + "\n")
