# Changelog

All notable changes to vLLM Manager will be documented in this file.

## [0.2.0] - 2026-02-27

### 🎉 Major Release - Complete Redesign

#### Changed
- **Architecture**: `VLLMInstance` now inherits from `vllm.engine.arg_utils.AsyncEngineArgs`
  - All vLLM parameters automatically supported without manual maintenance
  - No parameter drift between vLLM and vLLM Manager
  - Future vLLM features automatically supported

- **Process Management**: Uses official vLLM CLI
  - `python -m vllm.entrypoints.openai.api_server --model ...`
  - All vLLM parameters passed directly to official CLI

- **API Client**: Returns official OpenAI SDK client
  - `from openai import OpenAI`
  - Seamless integration with existing code
  - No custom HTTP wrappers

#### Added
- `served_model_name` property - extracts model name from path
  - `Qwen/Qwen2.5-1.5B-Instruct` → `Qwen2.5-1.5B-Instruct`
  - Easy identification of models in multi-instance setups

- Log file naming includes model name and port
  - Format: `vllm_{model_name}_{port}_{timestamp}.log`
  - Easy to identify which model each server is running

- `requirements.txt` with dependencies
  - vllm>=0.7.0
  - openai>=1.0.0
  - requests>=2.28.0

- Load balancing with automatic failover
- Health monitoring and auto-retry
- Automatic log capture and aggregation

#### Removed
- Manual parameter definitions (`VLLMConfig` class)
- Custom HTTP request wrappers
- Router module (replaced by LoadBalancedClient)

#### Documentation
- Complete README rewrite following standard open-source format
- Added multi-model usage examples
- Enhanced FAQ section
- Updated API reference

---

## [0.1.0] - 2026-02-26

### Initial Release

- Basic vLLM process management
- Multi-server cluster support
- Health check functionality
