# FlowPilot – AI-Powered Engineering Assistant for GNU Radio Companion

**FlowPilot** is an AI-native engineering assistant developed to integrate intelligent assistance directly into **GNU Radio Companion (GRC)**. It aims to simplify GNU Radio development by combining flowgraph inspection, validation, DSP research assistance, block-level analysis, and AI-assisted engineering workflows within the GRC environment.

Instead of constantly switching between GNU Radio Companion, documentation, research papers, and external AI tools, FlowPilot brings these capabilities into an integrated sidebar interface.

## Overview

GNU Radio Companion is a visual programming environment used to design and develop signal-processing and software-defined radio (SDR) systems.

Understanding complex flowgraphs, configuring blocks, identifying connection errors, and interpreting research papers can be challenging.

FlowPilot addresses these challenges through an integrated engineering assistant that helps users inspect their active flowgraphs, understand block configurations, identify potential issues, and explore DSP concepts.

## Key Features

### 1. GNU Radio Companion Integration
- Integrated assistant interface within GNU Radio Companion.
- Sidebar-based workflow that works alongside the GRC editor.
- Designed to preserve the existing flowgraph editing environment.
- Provides engineering assistance without requiring users to leave GRC.

### 2. AI-Powered Flowgraph Analysis
- Generate summaries of the active flowgraph.
- Explain flowgraph structure and signal-processing workflows.
- Inspect selected blocks and their configurations.
- Analyze block parameters, input/output ports, and connections.
- Provide engineering explanations for the current design.

### 3. Flowgraph Validation
- Inspect the active flowgraph.
- Identify structural errors and potential configuration issues.
- Check block parameters and connection consistency.
- Display validation results and engineering review suggestions.
- Provide recommendations for correcting detected issues.

### 4. Intelligent Block Assistance
- Inspect selected GNU Radio blocks.
- Retrieve block configuration details.
- Explore installed OFDM blocks through read-only inspection.
- Identify compatible blocks for potential connections.
- Support automatic connection workflows for compatible selected blocks.

### 5. Research Paper Analysis
- Attach and analyze research papers in PDF format.
- Ask technical questions about the loaded paper.
- Retrieve relevant passages using deterministic keyword-based matching.
- Present matching excerpts to help users verify information against the original paper.

**Note:** The paper-question feature shown in the prototype uses rule-based keyword matching rather than unrestricted AI-generated answers.

### 6. Local AI Model Integration
- Supports a local-model-assisted workflow.
- Qwen3 8B is shown as an available model in the interface.
- Separates research-supported information from general engineering explanations.
- Designed to support privacy-conscious local AI experimentation.

### 7. Flowgraph Design Assistance
- Explore flowgraph construction from research-paper plans.
- Support signal-processing workflow design.
- Provide suggestions for block selection and connectivity.
- Assist with understanding DSP and GNU Radio concepts.

## Technology Stack

- **GNU Radio Companion (GRC):** Visual SDR and signal-processing environment.
- **Python:** Core application and integration development.
- **PyQt / Qt:** Desktop interface and sidebar integration.
- **Large Language Models:** AI-assisted engineering explanations.
- **Qwen3 8B:** Local model integration demonstrated in the interface.
- **PDF Processing:** Research-paper text extraction and analysis.
- **GNU Radio Blocks:** Flowgraph inspection and engineering workflows.

## Architecture and Workflow

FlowPilot follows an integrated engineering-assistant workflow:

1. **GRC Environment:** The user opens or creates a GNU Radio flowgraph.
2. **Flowgraph Inspection:** FlowPilot examines the active graph and its blocks.
3. **Validation:** Deterministic checks identify structural issues and warnings.
4. **Engineering Analysis:** The assistant helps explain the graph and its configuration.
5. **Research Assistance:** Users can attach research papers and investigate relevant technical passages.
6. **Design Support:** The assistant provides suggestions for block selection and workflow construction.

## Example Capabilities

The prototype demonstrates:

- Flowgraph summaries.
- Selected block inspection.
- AI-assisted flowgraph explanations.
- Active flowgraph validation.
- Installed OFDM block inspection.
- Automatic compatible-block connection support.
- Research-paper question interface.
- Local Qwen3 8B model selection.
- Validation reports with structural errors and warnings.

## Project Status

**Status: Research and Development Prototype**

FlowPilot is an ongoing engineering project. Its features are being developed and tested within GNU Radio Companion.

Some capabilities may require additional configuration or further development before they are suitable for production use.

## Future Development

- Improved contextual understanding of complex DSP flowgraphs.
- More reliable research-paper question answering with source citations.
- Advanced DSP block recommendations.
- Better automated flowgraph construction.
- Enhanced error diagnosis and correction suggestions.
- Improved integration with local and cloud-based AI models.
- Expanded support for SDR and OFDM engineering workflows.

## Learning Outcomes

This project explores the intersection of:

- Artificial Intelligence and Agentic Engineering Tools.
- Software-Defined Radio.
- Digital Signal Processing.
- GNU Radio Companion Integration.
- Python Desktop Application Development.
- Large Language Model Integration.
- Automated Engineering Validation.
- Research-Paper-Assisted Engineering.

## Author

**P. Harsha Vardhan Reddy**

B.Tech – Artificial Intelligence and Data Science  (CPS&S)
Amrita Vishwa Vidyapeetham

---

**FlowPilot – Bringing AI-Assisted Engineering Workflows into GNU Radio Companion.**
