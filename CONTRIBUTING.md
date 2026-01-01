# Contributing to Lár

First off — thank you!  
Lár aims to become the *PyTorch of Agent Reasoning*, and community contributions are essential.

## How to Contribute
### 1. Fork the repository  
### 2. Create a feature branch  

```bash
git checkout -b feature/my-feature
```
### 3. Add tests  
Lár emphasizes reliability and auditability.  
Every new feature *must* include tests.

### 4. Ensure logs remain deterministic  
Do not modify log structures in a breaking way.

### 5. Submit a PR  
Include:
- ⁠What the feature does  
- Why it’s needed  
- ⁠Before/After behavior  
- Example usage  

We review PRs weekly.

## Code Style  
- ⁠Python 3.10+  
- ⁠Pydantic for schemas  
- ⁠Type hints required  
- ⁠Avoid unnecessary abstraction  
- ⁠Keep the “Glass Box” philosophy: everything should be inspectable  

Thanks again — you’re shaping the future of agents.