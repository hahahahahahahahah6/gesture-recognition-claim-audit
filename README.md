# Documentation claim auditor

Offline, deterministic, standard-library-only inspection of documentation about
hand signals from camera input and sign decoding. Requires Python 3.9 or later.
No network, telemetry, model execution, or file writes are performed.

## Usage

```sh
python3 -m pip install .
gesture-recognition-claim-audit audit .
python3 -m gesture_recognition_claim_audit audit . --json
gesture-recognition-claim-audit audit . --verbose --ignore vendor/ --ignore examples/
gesture-recognition-claim-audit audit . --fail-on medium
gesture-recognition-claim-audit --version
```

The repository defaults to the current directory. Exit status is 0 when no
finding reaches the threshold, 2 when one does, and 1 for usage or IO errors.
The default threshold is high. JSON emits a list of findings with id, severity,
path, verdict, message, and phrases. Verbose scope and per-file decisions go to
standard error. Repeatable ignore prefixes match repository-relative paths.

## Scope and rules

Scans the root README and Markdown below docs. Claims in files under a tests
directory receive medium severity. Python sources are inspected throughout the
repository, excluding version control, bytecode caches, virtual environments,
and build output. Each evidence route must be complete in one module. Imported
aliases, simple assigned aliases, and chained calls are supported. Local function
and class definitions shadow imported names. Unparseable modules supply no evidence.

Fenced code is excluded; inline code counts as prose. Matching uses exact,
case-insensitive substrings without stemming or hyphen normalization. Denial
spans are removed first. Longest-first matching blanks spans so each occurrence
matches once under its longest phrase. A claim without evidence is high severity;
a denial contradicted by evidence is high severity. A denial without evidence
passes. Findings use these identifiers:

```text
documented-gesture-recognition-claim-false
documented-no-gesture-recognition-claim-false
```

## Differentiation

The following tools respectively check recognising whole-body actions over time,
locating body joints, and decoding ink on the page:

```text
action-recognition-claim-audit
pose-estimation-claim-audit
handwriting-recognition-claim-audit
```

This auditor checks classifying a hand gesture from camera or sensor input.
Those neighboring capabilities alone do not establish the checked feature.

## Evidence and limitations

Static pattern matching is not semantic judgement. Exact phrases miss restatements.
Generic calls on unrelated objects count because their method names are shared:

```python
unrelated.recognize_gesture()
```

A bare generic call needs a matching from-import. The first pair below requires
construction plus a recognize call on the returned instance, assigned or chained.
This shows the checked feature is used, not that classifications are correct.
The second pair counts although hand landmarks are the input stage of the checked
feature, not classification itself:

```text
MediaPipe GestureRecognizer + recognize / recognize_for_video / recognize_async
MediaPipe Hands + .process(
```

The contour route requires both calls in one module. The sensor route requires
construction followed by a gesture read on a frame from that controller:

```text
cv2.findContours + cv2.convexityDefects
Leap.Controller + .frame().gestures(
```

Touch-screen swipe, pinch, and tap handlers are deliberately not counted because
they recognise touch input rather than hand gestures from camera or sensor input.
The first three phrases below can also describe a person reading someone else's
gestures. The fourth can describe touch-screen handling rather than the checked
capability from camera input:

```text
read gestures
reads gestures
reading gestures
gesture recognition
```

The auditor cannot distinguish those meanings. Control flow and runtime types
are not evaluated. Bare imports, strings, comments, docstrings, subprocess CLI
commands, setup alone, and evidence split across modules do not count. Joint
estimation, face analysis, and object detection alone do not qualify. No model
quality or prediction correctness is verified.

## Development

```sh
python3 -m unittest discover
python3 -m build
```

Distributed under the MIT license.
