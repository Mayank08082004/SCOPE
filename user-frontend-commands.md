### Real-Time Interactive Demo and Result Visualization of SCOPE Simulator
#### Install Dependencies
Make sure you have Python and Node.js installed, then run:
```bash
pip install -r requirements.txt
cd frontend && npm install
```

#### Start Frontend Server (Keep Running)
In your terminal, navigate to the frontend directory and start Vite:
```bash
cd frontend
npm run dev
```
This will host the React app on `http://localhost:5173`.

#### Run Backend (Keep Running)
Open a new terminal (do not stop the previous one), then run:
```bash
python3 app.py
```
This will host the Flask API on `http://localhost:5001`.
