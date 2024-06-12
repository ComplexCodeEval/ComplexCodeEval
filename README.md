# ComplexCodeEval

ComplexCodeEval is an evaluation benchmark designed to accommodate multiple downstream tasks, accurately reflect different programming environments, and deliberately avoid data leakage issues. This benchmark includes a diverse set of samples from real-world projects, aiming to closely mirror actual development scenarios.

## Overview

ComplexCodeEval consists of:
- **3,897 Java samples** from **1,055 code repositories**
- **7,184 Python samples** from **2,107 code repositories**

### Key Features

1. **Diverse Downstream Tasks**: The benchmark supports multiple downstream tasks to evaluate the performance of different code analysis tools and models.
2. **Accurate Reflection of Programming Environments**: Samples are selected from projects that use popular third-party frameworks and packages.
3. **Avoidance of Data Leakage**: Incorporates multiple timestamps for each sample to prevent data leakage.

## Data Collection Process

To ensure the benchmark is representative of real-world development scenarios, we followed these steps:

1. **Screening Frameworks and Packages**: We screened 69 popular Java third-party frameworks and 55 popular Python third-party packages based on their SourceRank from Libraries.io. These cover a wide range of fields, including:
   - Web development
   - Network communication
   - Data processing and persistence
   - Security and encryption
   - ...

2. **Selecting Repositories**: High-star code repositories that depend on these libraries were selected from GitHub.

3. **Analyzing and Extracting Samples**: We analyzed the code repositories, tracked the usage of each library’s API, and extracted functions that rely on high-frequency APIs as samples.

### Annotations

Each sample in ComplexCodeEval includes various annotations:
- Test cases
- Reference APIs
- Docstrings
- Multiple timestamps (project creation time, file creation time, and function update time)
- ...