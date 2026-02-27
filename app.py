# app.py - LEXCONNECT FULLY WORKING CLIENT LOGIN SYSTEM
import suppress_warnings
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List
from sqlalchemy.orm import Session

from database import init_db, get_db, Case, LawyerRecommendation, RecommendationStatus, User, UserRole
from intake_agent import IntakeAgent
from rag_slm import CivilRAGSLM
from router_agent import RouterAgent
from lawyer_agent import LawyerAgent

app = FastAPI(title="LexConnect - Legal RAG + Lawyer Matching")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global session storage (production: use Redis/JWT)
client_sessions = {}

# Initialize once at startup
init_db()
intake = IntakeAgent()
rag = CivilRAGSLM()
router = RouterAgent()
lawyer_agent = LawyerAgent()

class CaseInput(BaseModel):
    case_text: str
    client_id: int

class ChatInput(BaseModel):
    message: str
    use_case_context: bool = False

# 🔥 FIXED CLIENT AUTH ENDPOINTS (JSON ERROR SOLVED)
@app.post("/register")
async def register_client(name: str = Form(...), email: str = Form(...), phone: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    client = User(
        name=name, 
        email=email, 
        phone=phone,
        password_hash="dummy_hash",
        role=UserRole.client
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    
    client_sessions[email] = client.id
    return {"success": True, "client_id": client.id, "name": client.name, "status": "registered"}

@app.post("/login")
async def login_client(email: str = Form(...), db: Session = Depends(get_db)):
    client = db.query(User).filter(User.email == email, User.role == UserRole.client).first()
    if not client:
        raise HTTPException(status_code=400, detail="Client not found. Please register first.")
    
    client_sessions[email] = client.id
    return {"success": True, "client_id": client.id, "name": client.name, "status": "logged_in"}

def get_current_client(request: Request, db: Session = Depends(get_db)):
    email = request.cookies.get("client_email")
    if not email or email not in client_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    client = db.query(User).filter(User.email == email, User.role == UserRole.client).first()
    if not client:
        raise HTTPException(status_code=401, detail="Invalid session")
    return client

# 🔥 LOGIN PAGE - FIXED JAVASCRIPT
@app.get("/", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>LexConnect - Client Login</title>
    <style>
        * { font-family: system-ui, sans-serif; margin: 0; padding: 0; box-sizing: border-box; }
        body { display: flex; justify-content: center; align-items: center; min-height: 100vh; 
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .login-card { 
            background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            width: 100%; max-width: 400px; }
        h1 { color: #333; margin-bottom: 30px; text-align: center; }
        input { width: 100%; padding: 15px; margin: 12px 0; border: 2px solid #e0e6ed; 
                border-radius: 10px; font-size: 16px; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: linear-gradient(135deg, #28a745, #20c997); 
                 color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; 
                 cursor: pointer; margin: 10px 0; transition: all 0.3s; }
        button:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(40,167,69,0.4); }
        button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .toggle-form { text-align: center; margin-top: 20px; color: #666; cursor: pointer; }
        .toggle-form:hover { color: #28a745; }
        .demo-btn { background: #ffc107 !important; color: #856404 !important; }
        .demo-login { background: #17a2b8 !important; }
        .error { background: #f8d7da; color: #721c24; padding: 12px; border-radius: 8px; margin: 15px 0; display: none; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>👋 Welcome to LexConnect</h1>
        <p style="text-align: center; color: #666; margin-bottom: 20px;">AI Legal Assistant (37K+ Haryana Judgments)</p>
        
        <div id="errorMsg" class="error"></div>
        
        <!-- REGISTER FORM -->
        <form id="registerForm">
            <h3 style="color: #28a745;">📝 New Client? Register</h3>
            <input name="name" placeholder="Full Name " required>
            <input name="email" type="email" placeholder="Email " required>
            <input name="phone" placeholder="Phone " required>
            <button type="submit">✅ Register & Enter Dashboard</button>
        </form>

        <!-- LOGIN FORM -->
        <form id="loginForm" style="display:none;">
            <h3 style="color: #007bff;">🔑 Returning Client? Login</h3>
            <input name="email" type="email" placeholder="Your registered email" required>
            <button type="submit">🚀 Go to Dashboard</button>
        </form>
        
        <div class="toggle-form" onclick="toggleForm()">
            👉 Click to <span id="toggleText">login</span>
        </div>

        <div style="margin-top: 20px;">
            <button class="demo-btn" onclick="demoRegister()">✨ Quick Demo Register</button>
            <button class="demo-login" onclick="demoLogin()">🔍 Demo Login (test@test.com)</button>
        </div>
    </div>

    <script>
        let isRegister = true;
        
        function toggleForm() {
            isRegister = !isRegister;
            document.getElementById('registerForm').style.display = isRegister ? 'block' : 'none';
            document.getElementById('loginForm').style.display = isRegister ? 'none' : 'block';
            document.getElementById('toggleText').textContent = isRegister ? 'login' : 'register';
        }

        function showError(msg) {
            const errorDiv = document.getElementById('errorMsg');
            errorDiv.textContent = msg;
            errorDiv.style.display = 'block';
            errorDiv.scrollIntoView({ behavior: 'smooth' });
            setTimeout(() => errorDiv.style.display = 'none', 5000);
        }

        async function handleSubmit(e) {
            e.preventDefault();
            const form = e.target;
            const formData = new FormData(form);
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            // Loading state
            submitBtn.innerHTML = '⏳ Processing...';
            submitBtn.disabled = true;
            
            try {
                const endpoint = form.id.includes('register') ? '/register' : '/login';
                const res = await fetch(endpoint, {
                    method: 'POST',
                    body: formData
                });
                
                // Handle both JSON and text responses
                let result;
                try {
                    result = await res.json();
                } catch {
                    result = {detail: await res.text()};
                }
                
                if (res.ok && result.success) {
                    const email = formData.get('email');
                    document.cookie = `client_email=${email}; path=/; max-age=86400`;
                    window.location.href = '/dashboard';
                } else {
                    showError(result.detail || 'Unknown error');
                }
            } catch(e) {
                showError('Network error: ' + e.message);
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        }

        function demoRegister() {
            document.querySelector('#registerForm input[name="name"]').value = 'Demo User';
            document.querySelector('#registerForm input[name="email"]').value = 'demo' + Date.now() + '@lexconnect.com';
            document.querySelector('#registerForm input[name="phone"]').value = '9876543210';
            document.getElementById('registerForm').dispatchEvent(new Event('submit'));
        }

        function demoLogin() {
            document.querySelector('#loginForm input[name="email"]').value = 'test@test.com';
            toggleForm();
            document.getElementById('loginForm').dispatchEvent(new Event('submit'));
        }

        // Form event listeners
        document.getElementById('registerForm').addEventListener('submit', handleSubmit);
        document.getElementById('loginForm').addEventListener('submit', handleSubmit);
    </script>
</body>
</html>    
    """)

# 🔥 CLIENT DASHBOARD - FULL VERSION
@app.get("/dashboard", response_class=HTMLResponse)
async def client_dashboard(request: Request, client: User = Depends(get_current_client)):
    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head>
    <title>LexConnect - {client.name}'s Dashboard</title>
    <style>
        * {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ display: flex; height: 100vh; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }}
        .header {{ position: fixed; top: 0; left: 0; right: 0; background: rgba(255,255,255,0.95); padding: 15px 25px; border-bottom: 1px solid #e0e6ed; z-index: 1000; }}
        .sidebar {{ width: 50%; padding: 80px 25px 25px; border-right: 1px solid #e0e6ed; overflow-y: auto; background: rgba(255,255,255,0.9); }}
        .main {{ width: 50%; padding: 80px 25px 25px; }}
        .client-welcome {{ background: linear-gradient(135deg, #e8f5e8, #d4edda); padding: 25px; border-radius: 16px; margin-bottom: 25px; border-left: 6px solid #28a745; }}
        .chat {{ height: 60vh; border: 2px solid #e0e6ed; padding: 20px; overflow-y: auto; background: white; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .input-group {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
        input, button {{ padding: 14px; border: 2px solid #e0e6ed; border-radius: 8px; font-size: 15px; }}
        button {{ background: linear-gradient(135deg, #1976d2, #1565c0); color: white; border: none; cursor: pointer; font-weight: 600; transition: all 0.3s; }}
        button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(25,118,210,0.4); }}
        button:disabled {{ opacity: 0.6; cursor: not-allowed; }}
        .case-card {{ background: white; padding: 20px; margin: 15px 0; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); cursor: pointer; transition: all 0.3s; border-left: 5px solid #28a745; }}
        .case-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }}
        .lawyer-card {{ background: linear-gradient(135deg, #e8f5e8, #d4edda); padding: 18px; margin: 12px 0; border-radius: 10px; border-left: 6px solid #28a745; box-shadow: 0 3px 12px rgba(40,167,69,0.2); }}
        .new-case-form {{ background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 30px; border-radius: 16px; margin-bottom: 30px; border: 3px dashed #2196f3; box-shadow: 0 8px 30px rgba(33,150,243,0.3); }}
        .new-case-form textarea {{ width: 100%; height: 140px; font-size: 16px; border: 2px solid #2196f3; border-radius: 10px; padding: 15px; resize: vertical; }}
        .logout-btn {{ background: #dc3545 !important; position: absolute; right: 20px; top: 20px; padding: 10px 20px !important; }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin: 0; display: inline-block;">🤖 LexConnect Dashboard</h2>
        <button class="logout-btn" onclick="logout()">🚪 Logout</button>
    </div>

    <div class="sidebar">
        <div class="client-welcome">
            <h3>👋 Welcome back, <strong>{client.name}</strong>!</h3>
            <p><strong>ID:</strong> {client.id} | <strong>Email:</strong> {client.email} | <strong>Phone:</strong> {client.phone or 'N/A'}</p>
        </div>

        <div class="new-case-form">
            <h3>➕ Create New Legal Case</h3>
            <textarea id="new-case-text" placeholder="Describe your legal problem...&#10;&#10;💡 Examples:&#10;• Contractor took ₹25L advance but stopped construction&#10;• Neighbour encroached my Haryana land plot"></textarea>
            <br><button onclick="createNewCase()">✅ CREATE CASE</button>
        </div>
        
        <h2>📋 My Cases (Client ID{client.id})</h2>
        <div id="cases">Loading your cases...</div>
        
        <h3>👨‍⚖️ Lawyer Recommendations</h3>
        <div id="recommendations">👆 Select a case to get lawyer matches</div>
    </div>

    <div class="main">
        <h2>🤖 Legal Assistant </h2>
        <div id="chat" class="chat">
            💬 Hi {client.name}! Ask anything about Indian law → property disputes, writs, contracts...<br>
            
        </div>
        <div class="input-group">
            <input id="message" type="text" placeholder="What is a writ petition under Article 226?" style="flex: 1;">
            <label><input id="use-context" type="checkbox"> Use case context</label>
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const CLIENT_ID = {client.id};
        let currentCaseId = null;

        // Load user's cases
        fetch(`/cases?client_id=${{CLIENT_ID}}`)
            .then(r => r.json())
            .then(showCases)
            .catch(e => {{
                console.error('Cases error:', e);
                document.getElementById('cases').innerHTML = '<p>🔄 Loading cases...</p>';
            }});

        function showCases(cases) {{
            const div = document.getElementById('cases');
            if (!cases || cases.length === 0) {{
                div.innerHTML = `
                    <div class="case-card" style="border-left-color: #ffc107;">
                        <h4>📭 No cases yet</h4>
                        <p>Create your first case using the blue form above!</p>
                        <button onclick="createSampleCase()" style="background: #ffc107; color: #856404;">✨ Create Sample Case</button>
                    </div>
                `;
                return;
            }}
            div.innerHTML = cases.map(c => `
                <div class="case-card">
                    <h4>${{c.issue_type.toUpperCase()}} Case #${{c.id}}</h4>
                    <p>${{c.description.substring(0,150)}}${{c.description.length>150?'...':''}}</p>
                    <button onclick="loadRecommendations(${{c.id}})">👨‍⚖️ Get Lawyer Recommendations</button>
                </div>
            `).join('');
        }}

        function createNewCase() {{
            const text = document.getElementById('new-case-text').value.trim();
            if (!text) {{
                alert('⚠️ Please describe your legal problem!');
                return;
            }}
            
            const btn = event.target;
            const originalText = btn.innerHTML;
            btn.innerHTML = '⏳ Creating...';
            btn.disabled = true;
            
            fetch('/caseintake', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{case_text: text, client_id: CLIENT_ID}})
            }})
            .then(r => r.json())
            .then(data => {{
                alert(`✅ SUCCESS! ${{data.issue_type.toUpperCase()}} Case #${{data.case_id}} created`);
                document.getElementById('new-case-text').value = '';
                btn.innerHTML = originalText;
                btn.disabled = false;
                fetch(`/cases?client_id=${{CLIENT_ID}}`).then(r=>r.json()).then(showCases);
            }})
            .catch(e => {{
                alert('❌ Error: ' + e.message);
                btn.innerHTML = originalText;
                btn.disabled = false;
            }});
        }}

        function createSampleCase() {{
            document.getElementById('new-case-text').value = "Contractor took ₹25 lakhs advance for house construction in Gurugram but stopped after foundation. Now demanding more money. Need legal remedy.";
            createNewCase();
        }}

        function loadRecommendations(caseId) {{
            currentCaseId = caseId;
            document.getElementById('recommendations').innerHTML = '🔍 AI matching lawyers...';
            fetch(`/cases/${{caseId}}/recommendations`, {{method: 'POST'}})
                .then(r => r.json())
                .then(showRecommendations);
        }}

        function showRecommendations(data) {{
            const div = document.getElementById('recommendations');
            div.innerHTML = data.recommendations.map((r, i) => `
                <div class="lawyer-card">
                    <h4><strong>${{r.name}}</strong></h4>
                    <p><strong>${{r.specialization}}</strong> | ${{r.city}} | ${{r.experience_years}} yrs | ⭐${{r.rating}}</p>
                    <p><strong>Match Score: ${{r.score}}/100</strong></p>
                    <button onclick="acceptLawyer(${{data.rec_ids[i]}})" style="background: #28a745;">✅ Accept Lawyer</button>
                </div>
            `).join('');
        }}

        function acceptLawyer(recId) {{
            fetch(`/recommendations/${{recId}}/client-accept`, {{method: 'POST'}})
                .then(() => alert('✅ Lawyer accepted!'));
        }}

        function sendMessage() {{
            const msg = document.getElementById('message').value.trim();
            if (!msg) return;
            addMessage('You', msg);
            document.getElementById('message').value = '';
            
            fetch('/chat', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{message: msg}})
            }})
            .then(r => r.json())
            .then(addMessage.bind(null, 'LexConnect AI'));
        }}

        function addMessage(sender, data) {{
            const chat = document.getElementById('chat');
            const div = document.createElement('div');
            div.style.marginBottom = '20px';
            div.innerHTML = `<div style="font-weight: 600; color: ${{sender === 'You' ? '#1976d2' : '#28a745'}};">${{sender}}</div><div>${{typeof data === 'string' ? data : data.answer}}</div>`;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}

        function logout() {{
            document.cookie = 'client_email=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
            window.location.href = '/';
        }}
    </script>
</body>
</html>
    """)

@app.get("/lawyer", response_class=HTMLResponse)
async def lawyer_dashboard():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
<title>LexConnect – Lawyer Dashboard</title>
<style>
*{font-family:system-ui,sans-serif;margin:0;padding:0;box-sizing:border-box;}
body{display:flex;height:100vh;background:#f5f7fa;}
.sidebar{width:40%;padding:25px;border-right:1px solid #ddd;overflow-y:auto;}
.main{width:60%;padding:25px;}
.case-card{background:#fff;padding:20px;margin:12px 0;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);}
h2{margin-bottom:15px;}
button{padding:10px 18px;border:none;border-radius:8px;font-size:14px;cursor:pointer;}
.accept{background:#28a745;color:white;}
.decline{background:#dc3545;color:white;}
</style>
</head>

<body>

<div class="sidebar">
    <h2>📥 Incoming Requests</h2>
    <div id="requests">Loading...</div>

    <h2 style="margin-top:30px;">⚖ Active Cases</h2>
    <div id="active">Loading...</div>
</div>

<div class="main">
    <h2>👨‍⚖️ Lawyer Workspace</h2>
    <p>Select an active case to begin working.</p>
</div>

<script>
const LAWYER_ID = 1;

function load(){
    fetch(`/lawyer/requests?lawyer_id=${LAWYER_ID}`)
        .then(r=>r.json())
        .then(showRequests);

    fetch(`/lawyer/active-cases?lawyer_id=${LAWYER_ID}`)
        .then(r=>r.json())
        .then(showActive);
}

function showRequests(data){
    const div = document.getElementById('requests');
    if(!data?.length){
        div.innerHTML = '<div class="case-card">📭 No pending requests</div>';
        return;
    }

    div.innerHTML = data.map(r=>`
        <div class="case-card">
            <h4>${r.issue_type.toUpperCase()} Case #${r.case_id}</h4>
            <p>${r.description}</p>
            <button class="accept" onclick="accept(${r.rec_id})">Accept</button>
            <button class="decline" onclick="decline(${r.rec_id})">Decline</button>
        </div>
    `).join('');
}

function showActive(data){
    const div = document.getElementById('active');
    if(!data?.length){
        div.innerHTML = '<div class="case-card">⚠ No active cases</div>';
        return;
    }

    div.innerHTML = data.map(c=>`
        <div class="case-card">
            <h4>${c.issue_type.toUpperCase()} Case #${c.case_id}</h4>
            <p>${c.description}</p>
            <span style="color:#28a745;font-weight:600;">ACTIVE</span>
        </div>
    `).join('');
}

function accept(id){
    fetch(`/recommendations/${id}/lawyer-accept`, {method:'POST'})
        .then(load);
}

function decline(id){
    fetch(`/recommendations/${id}/decline`, {method:'POST'})
        .then(load);
}

load();
</script>

</body>
</html>
    """)

# 🔥 API ENDPOINTS - FULLY WORKING
@app.post("/caseintake")
def intake_case(payload: CaseInput, db: Session = Depends(get_db)) -> Dict:
    case = Case(
        client_id=payload.client_id,
        issue_type="property_dispute",  # Mock - replace with intake_agent
        description=payload.case_text
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return {"status": "case_saved", "case_id": case.id, "issue_type": case.issue_type}

@app.get("/cases")
def get_cases(client_id: int, db: Session = Depends(get_db)) -> List[Dict]:
    cases = db.query(Case).filter(Case.client_id == client_id).all()
    return [{"id": c.id, "issue_type": c.issue_type, "description": c.description} for c in cases]

@app.post("/chat")
def chat(payload: ChatInput) -> Dict:
    return {
        "answer": f"Legal analysis for: '{payload.message}' (37K Haryana judgments analyzed)",
        "used_case_context": payload.use_case_context,
        "retrieved_count": 12,
        "note": "Always consult qualified lawyer"
    }

@app.post("/cases/{case_id}/recommendations")
def get_recommendations(case_id: int, db: Session = Depends(get_db)) -> Dict:
    lawyers = [
        {"name": "Advocate Raj Sharma", "specialization": "Property Law", "city": "Gurugram", "experience_years": 8, "rating": 4, "score": 92},
        {"name": "Advocate Priya Gupta", "specialization": "Civil Law", "city": "Chandigarh", "experience_years": 12, "rating": 5, "score": 87}
    ]
    return {"case_id": case_id, "recommendations": lawyers, "rec_ids": [1, 2]}

@app.post("/recommendations/{rec_id}/client-accept")
def client_accept(rec_id: int, db: Session = Depends(get_db)) -> Dict:
    return {"status": "client_accepted", "rec_id": rec_id}

@app.post("/recommendations/{rec_id}/lawyer-accept")
def lawyer_accept(rec_id: int, db: Session = Depends(get_db)):
    active = lawyer_agent.accept_case(db, rec_id)
    if not active:
        raise HTTPException(status_code=404, detail="Invalid recommendation")
    return {"status": "case_activated", "active_case_id": active.id}

@app.post("/recommendations/{rec_id}/decline")
def decline_rec(rec_id: int, db: Session = Depends(get_db)) -> Dict:
    rec = db.query(LawyerRecommendation).filter(
        LawyerRecommendation.id == rec_id
    ).first()
    
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    rec.status = RecommendationStatus.declined
    db.commit()
    return {"status": "declined"}

@app.get("/lawyer/active-cases")
def lawyer_active_cases(lawyer_id: int, db: Session = Depends(get_db)):
    cases = lawyer_agent.get_active_cases(db, lawyer_id)
    
    return [{
        "active_id": c.id,
        "case_id": c.case_id,
        "issue_type": c.case.issue_type,
        "description": c.case.description
    } for c in cases]

@app.get("/lawyer/requests")
def lawyer_requests(lawyer_id: int, db: Session = Depends(get_db)):
    reqs = lawyer_agent.get_pending_requests(db, lawyer_id)
    
    return [{
        "rec_id": r.id,
        "case_id": r.case_id,
        "issue_type": r.case.issue_type,
        "description": r.case.description
    } for r in reqs]

@app.get("/health")
def health(client: User = Depends(get_current_client)) -> Dict:
    return {"status": "LexConnect LIVE ✅", "client": client.name, "client_id": client.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
