---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''
---

# Bug Report

**IMPORTANT: Please review the
[Issue Guidelines](https://github.com/Nuitka/Nuitka/blob/develop/CONTRIBUTING.md#submitting-an-issue)
before submitting.**

______________________________________________________________________

## ⚠️ Pre-Submission Checklist

*Please check these items before submitting your report. This text can be removed.*

- [ ] **Search Existing Issues:** Has this bug already been reported or fixed? Sometimes reports you
  find are bad, always feel free to make a better one, but reference what you found.
- [ ] **Python vs. Nuitka:** Does the issue occur when running the code with standard Python? If
  yes, it's not a Nuitka-specific issue, do not report it.
- [ ] **Test `develop` Branch:** Have you tried the `develop` version of Nuitka? It might contain a
  fix. Get it here https://nuitka.net/doc/download.html

______________________________________________________________________

**Discard everything above this line before submitting your issue.**

## 🐛 Bug Description

*(A clear and concise description of what the bug is.)*

## 🖥️ Environment

### 1. Nuitka Version, Python Version, OS, and Platform

**Provide the full output** of this command (replace `python` with your specific interpreter if
needed, e.g. `python_t`, for free-threading or `python_d` for debug Python):

```sh
python -m nuitka --version
```

*(Issues without this full output will be considered `invalid` as it contains crucial information
always required for diagnosis.)*

### 2. How Nuitka and Python were Installed

*(e.g., pip, anaconda, deb, rpm, from source, git clone, virtualenv used?)*

### 3. Relevant PyPI Packages and Versions

If specific packages are involved (e.g., `numpy`), list their names and versions. Shorten the output
of `python -m pip list -v` to only include relevant packages, but in doubt a longer list is not
necessarily harmful.

```sh
python -m pip list -v
```

## 🛠️ To Reproduce

### 1. "Hello World" Test (if applicable)

If you suspect a setup issue, first try compiling a simple `print("hello world")` program. If that
fails, report that error instead. *(We don't want a "Tensorflow does not work" report if basic
compilation fails. Please also consult the User Manual for supported setups.)*

### 2. Short, Self-Contained, Correct, Eligible (SSCCE) Example

Provide a minimal code example that reproduces the issue. It should have as few external
dependencies as possible. *(Issues without a clear, runnable example are likely to be rejected. For
packaging issues, a simple import might suffice. Repositories with `pipenv` or archives with small
examples are very welcome, but must contain only source code. Ensure usage is obvious; a compile
script is ideal. For non-commercial users, keep the code brief.)*

```python
# Your SSCCE code here
```

### 3. Nuitka Command Line Options

State the Nuitka options used. Ideally, use `# nuitka-project:` options in your code.

```python
# nuitka-project: --your-option=value
# nuitka-project: --another-option
```

Or, list the command line:

```sh
# Your Nuitka command here
# e.g., python -m nuitka --standalone your_script.py
```

**Important Notes on Options:**

- **Avoid all unnecessary options:**
  - Do **not** use `--deployment`. It disables bug-catching features. Remove it if you encounter an
    issue.
  - If the issue occurs with `--mode=standalone`, do not report it with `--mode=onefile` unless the
    problem is specific to onefile. State if the issue also occurs in standalone mode if you report
    a onefile issue.
  - Minimize options used. Do not use `--quiet` or disable warnings.

## 📉 Expected Behavior

*(A clear and concise description of what you expected to happen.)*

## 📄 Actual Behavior & Output

*(What actually happened? Include any error messages, tracebacks, or relevant logs. Use code blocks
for long outputs (triple backticks).*

## ↩️ Regression (if applicable)

Did this work in a previous version of Nuitka? If so, *please* specify the last known working
version. *(This helps dramatically in isolating the issue, e.g., via `git bisect`.)*

## 💡 Additional Context (Optional)

*(Add any other context about the problem here.)*

______________________________________________________________________

## 🚫 Unwelcome Practices (Please Read)

- **No Screenshots of Text:** Do *not* post screenshots of code, errors, or console output unless
  absolutely necessary (e.g., a GUI display problem). Provide text directly so it's searchable and
  copyable. Reports without proper text are likely to be rejected.
- **Do Not Close Issues Yourself:** We will close issues once they are resolved in a stable release.
  If you find your issue is invalid, you may close it, and we will tag it as `invalid` or even
  delete it later.
- **Do Not Report Against `factory` Branch:** Unless specifically asked, avoid reporting issues
  found on the `factory` branch as it's often unstable. Discuss on Discord first.

______________________________________________________________________

## 💼 Commercial Support

Consider Nuitka commercial support for priority assistance, which also helps sustain Nuitka's
development. This allows for direct code sharing or paid time for issue resolution in your
environment.

______________________________________________________________________

**PLEASE REMOVE ALL TEMPLATE TEXT (INCLUDING THIS LINE) BEFORE SUBMITTING YOUR ISSUE.**
