# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Demonstration of Travel AI Conceirge using Agent Development Kit"""

from google.adk.agents import Agent
import os
import time
import google.generativeai as genai
from google.api_core import retry

from travel_concierge import prompt

from travel_concierge.sub_agents.booking.agent import booking_agent
from travel_concierge.sub_agents.in_trip.agent import in_trip_agent
from travel_concierge.sub_agents.inspiration.agent import inspiration_agent
from travel_concierge.sub_agents.planning.agent import planning_agent
from travel_concierge.sub_agents.post_trip.agent import post_trip_agent
from travel_concierge.sub_agents.pre_trip.agent import pre_trip_agent

from travel_concierge.tools.memory import _load_precreated_itinerary

# Disable OpenTelemetry to fix context detach errors
os.environ.setdefault('OTEL_SDK_DISABLED', 'true')
os.environ.setdefault('OTEL_TRACES_EXPORTER', 'none')
os.environ.setdefault('OTEL_METRICS_EXPORTER', 'none')
os.environ.setdefault('OTEL_LOGS_EXPORTER', 'none')

# Configure Gemini API with retry logic
def configure_genai():
    api_key = os.getenv('GOOGLE_CLOUD_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_CLOUD_API_KEY environment variable is not set")

    genai.configure(api_key=api_key)

    # List available models to verify access
    print("Checking available Gemini models...")
    for m in genai.list_models():
        print(f"Found model: {m.name}")

# Configure the API
configure_genai()

root_agent = Agent(
    model="gemini-2.0-flash-exp",
    name="root_agent",
    description="A Travel Conceirge using the services of multiple sub-agents",
    instruction=prompt.ROOT_AGENT_INSTR,
    sub_agents=[
        inspiration_agent,
        planning_agent,
        booking_agent,
        pre_trip_agent,
        in_trip_agent,
        post_trip_agent,
    ],
    before_agent_callback=_load_precreated_itinerary,
)
