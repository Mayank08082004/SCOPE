### Real-Time Interactive Demo and Result Visualization of SCOPE Simulator
#### Install Dependencies
Make sure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

#### Start Frontend Server (Keep Running)
In WSL/Linux terminal:
```bash
python3 -m http.server 8000
```
This will host your HTML files locally.

#### Open in Browser
Go to:
```bash
http://localhost:8000
```

#### Run Backend (Keep Running)
Open a new terminal (do not stop the previous one), then run:
```bash
python3 app.py
```
