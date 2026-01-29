# app.py - COMPLETE LEXCONNECT MVP (37k Vectors + Full Dashboard)
import suppress_warnings
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from database import init_db, get_db, Case, LawyerRecommendation, RecommendationStatus
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

# Initialize once at startup
init_db()
intake = IntakeAgent()
rag = CivilRAGSLM()
router = RouterAgent()
lawyer_agent = LawyerAgent()

class CaseInput(BaseModel):
    case_text: str
    client_id: Optional[int] = None

class ChatInput(BaseModel):
    message: str
    use_case_context: bool = False

@app.post("/caseintake")
def intake_case(payload: CaseInput, db: Session = Depends(get_db)) -> Dict:
    details = intake.extract_case_details(payload.case_text)
    case_id = intake.store_case_details(db, details, client_id=payload.client_id)
    return {
        "status": "case_saved",
        "case_id": case_id,
        "issue_type": details["issue_type"],
        "raw_description": details["raw_description"],
    }

@app.post("/chat")
def chat(payload: ChatInput) -> Dict:
    ctx = intake.get_case_context() if payload.use_case_context else None
    result = rag.answer(payload.message, case_context=ctx)
    return {
        "answer": result["answer"],
        "used_case_context": bool(ctx),
        "retrieved_count": result.get("retrieved_count", 0),
        "note": "Information only. Always verify with qualified lawyer."
    }

@app.post("/cases/{case_id}/recommendations")
def get_recommendations(case_id: int, db: Session = Depends(get_db)) -> Dict:
    """Get top 5 lawyer recommendations for a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    lawyers = router.get_top_lawyers(db, case.issue_type)
    rec_ids = router.create_recommendations(db, case_id, lawyers)
    
    return {
        "case_id": case_id,
        "issue_type": case.issue_type,
        "recommendations": lawyers,
        "rec_ids": rec_ids
    }

@app.get("/cases/{case_id}/recommendations")
def list_recommendations(case_id: int, db: Session = Depends(get_db)) -> List[Dict]:
    """List recommendations for a case."""
    recs = db.query(LawyerRecommendation).filter(
        LawyerRecommendation.case_id == case_id
    ).join(LawyerRecommendation.lawyer).all()
    
    result = []
    for rec in recs:
        result.append({
            "rec_id": rec.id,
            "lawyer_id": rec.lawyer_id,
            "name": rec.lawyer.user.name,
            "specialization": rec.lawyer.specialization or "General",
            "city": rec.lawyer.city or "N/A",
            "experience_years": rec.lawyer.experience_years or 0,
            "rating": rec.lawyer.rating or 0,
            "score": rec.score,
            "status": rec.status.value
        })
    return result

@app.post("/recommendations/{rec_id}/client-accept")
def client_accept(rec_id: int, db: Session = Depends(get_db)) -> Dict:
    """Client accepts a lawyer recommendation."""
    rec = db.query(LawyerRecommendation).filter(LawyerRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.status = RecommendationStatus.client_accepted
    db.commit()
    return {"status": "client_accepted", "rec_id": rec_id}

@app.post("/recommendations/{rec_id}/lawyer-accept")
def lawyer_accept(rec_id: int, db: Session = Depends(get_db)):
    active = lawyer_agent.accept_case(db, rec_id)
    if not active:
        raise HTTPException(404, "Invalid recommendation")
    return {"status": "case_activated", "active_case_id": active.id}

@app.get("/lawyer/active-cases")
def lawyer_active_cases(lawyer_id: int, db: Session = Depends(get_db)):
    cases = lawyer_agent.get_active_cases(db, lawyer_id)
    return [{
        "active_id": c.id,
        "case_id": c.case_id,
        "issue_type": c.case.issue_type,
        "description": c.case.description
    } for c in cases]

@app.post("/recommendations/{rec_id}/decline")
def decline_rec(rec_id: int, db: Session = Depends(get_db)) -> Dict:
    """Decline recommendation."""
    rec = db.query(LawyerRecommendation).filter(LawyerRecommendation.id == rec_id).first()
    if rec:
        rec.status = RecommendationStatus.declined
        db.commit()
    return {"status": "declined"}

# DASHBOARD ENDPOINTS
@app.get("/cases")
def get_cases(client_id: int, db: Session = Depends(get_db)) -> List[Dict]:
    """Get client's cases for dashboard."""
    cases = db.query(Case).filter(Case.client_id == client_id).all()
    return [{"id": c.id, "issue_type": c.issue_type, "description": c.description} for c in cases]

@app.get("/lawyer/requests")
def lawyer_requests(lawyer_id: int, db: Session = Depends(get_db)):
    reqs = lawyer_agent.get_pending_requests(db, lawyer_id)
    return [{
        "rec_id": r.id,
        "case_id": r.case_id,
        "issue_type": r.case.issue_type,
        "description": r.case.description
    } for r in reqs]
# 🔥 MAIN CLIENT DASHBOARD (FIXES 404 ERROR)
@app.get("/", response_class=HTMLResponse)
async def client_dashboard():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>LexConnect - AI Legal Assistant (Haryana)</title>
    <style>
        * { font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 0; box-sizing: border-box; }
        body { display: flex; height: 100vh; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .sidebar { width: 50%; padding: 25px; border-right: 1px solid #e0e6ed; overflow-y: auto; background: rgba(255,255,255,0.9); }
        .main { width: 50%; padding: 25px; }
        .chat { height: 65vh; border: 2px solid #e0e6ed; padding: 20px; overflow-y: auto; background: white; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .input-group { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        input, button { padding: 14px; border: 2px solid #e0e6ed; border-radius: 8px; font-size: 15px; }
        button { background: linear-gradient(135deg, #1976d2, #1565c0); color: white; border: none; cursor: pointer; font-weight: 600; transition: all 0.3s; }
        button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(25,118,210,0.4); }
        .case-card { background: white; padding: 20px; margin: 15px 0; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); cursor: pointer; transition: all 0.3s; border-left: 5px solid #28a745; }
        .case-card:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
        .lawyer-card { background: linear-gradient(135deg, #e8f5e8, #d4edda); padding: 18px; margin: 12px 0; border-radius: 10px; border-left: 6px solid #28a745; box-shadow: 0 3px 12px rgba(40,167,69,0.2); }
        .new-case-form { 
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
            padding: 30px; border-radius: 16px; margin-bottom: 30px; 
            border: 3px dashed #2196f3; box-shadow: 0 8px 30px rgba(33,150,243,0.3);
        }
        .new-case-form h3 { color: #1976d2; margin-bottom: 18px; font-size: 22px; font-weight: 700; }
        .new-case-form textarea { width: 100%; height: 140px; font-size: 16px; border: 2px solid #2196f3; border-radius: 10px; padding: 15px; resize: vertical; font-family: inherit; line-height: 1.5; }
        .status { padding: 8px 16px; border-radius: 25px; font-size: 13px; font-weight: bold; background: #fff3cd; color: #856404; }
        h2, h3 { color: #1a1a1a; margin-bottom: 18px; font-weight: 600; }
        label { font-size: 15px; cursor: pointer; user-select: none; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; }
        </style>
</head>
<body>
    
    
    <div class="sidebar">
        <div class="new-case-form">
            <h3>➕ <strong>Create New Legal Case</strong></h3>
            <textarea id="new-case-text" placeholder="Describe your legal problem in detail...&#10;&#10;💡 Examples:&#10;• 'Neighbour encroached 10ft on my Haryana land plot, built permanent wall'&#10;• 'Contractor took ₹25L advance for construction but abandoned site in Gurugram'&#10;• 'Husband filed false 498A case, need quashing in Punjab & Haryana HC'"></textarea>
            <br><button onclick="createNewCase()">✅ CREATE CASE</button>
        </div>
        
        <h2>📋 My Cases</h2>
        <div id="cases">Loading your cases...</div>
        
        <h3>👨‍⚖️ Lawyer Recommendations</h3>
        <div id="recommendations">👆 Select a case above to get lawyer matches</div>
    </div>
    
    <div class="main">
        <h2>🤖 Legal Assistant (37K+ Haryana Judgments)</h2>
        <div id="chat" class="chat">
            💬 Ask anything about Indian law → property disputes, writs, contracts, family matters...<br>
            📚 Powered by 37,134 Haryana High Court judgments<br>
            ⚡ Supports case-specific context (check box below)
        </div>
        <div class="input-group">
            <input id="message" type="text" placeholder="What is a writ petition under Article 226?" style="flex: 1;">
            <label><input id="use-context" type="checkbox"> Use case context</label>
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        let currentCaseId = null;
        
        // Load cases immediately
        fetch('/cases?client_id=789')
            .then(r => r.json())
            .then(showCases)
            .catch(e => {
                console.error('Cases error:', e);
                document.getElementById('cases').innerHTML = '<p>🔄 Loading cases... (check console)</p>';
            });
        
        function showCases(cases) {
            const div = document.getElementById('cases');
            if (!cases || cases.length === 0) {
                div.innerHTML = `
                    <div class="case-card" style="border-left-color: #ffc107; background: #fff8e1;">
                        <h4>📭 No cases yet</h4>
                        <p>Create your first case using the blue form above!<br>
                        <small>💡 Try: "Contractor took advance but stopped construction"</small>
                        </p>
                        <button onclick="createSampleCase()" style="background: #ffc107; color: #856404;">✨ Create Sample Case</button>
                    </div>
                `;
                return;
            }
            div.innerHTML = cases.map(c => `
                <div class="case-card">
                    <h4>${c.issue_type.toUpperCase()} Case #${c.id}</h4>
                    <p>${c.description.substring(0,150)}${c.description.length>150?'...':''}</p>
                    <button onclick="loadRecommendations(${c.id})">👨‍⚖️ Get Lawyer Recommendations</button>
                </div>
            `).join('');
        }
        
        function createNewCase() {
            const text = document.getElementById('new-case-text').value.trim();
            if (!text) {
                alert('⚠️ Please describe your legal problem!');
                return;
            }
            
            const btn = event.target;
            btn.textContent = '⏳ Creating...';
            btn.disabled = true;
            
            fetch('/caseintake', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({case_text: text, client_id: 789})
            })
            .then(r => r.json())
            .then(data => {
                alert(`✅ SUCCESS! ${data.issue_type.toUpperCase()} Case #${data.case_id} created`);
                document.getElementById('new-case-text').value = '';
                btn.textContent = '✅ CREATE CASE';
                btn.disabled = false;
                fetch('/cases?client_id=789').then(r=>r.json()).then(showCases);
            })
            .catch(e => {
                alert('❌ Error: ' + e.message);
                btn.textContent = '✅ CREATE CASE';
                btn.disabled = false;
            });
        }
        
        function createSampleCase() {
            document.getElementById('new-case-text').value = "Contractor took ₹25 lakhs advance for house construction in Gurugram but stopped after foundation. Now demanding more money. Need legal remedy.";
            createNewCase();
        }
        
        function loadRecommendations(caseId) {
            currentCaseId = caseId;
            const recDiv = document.getElementById('recommendations');
            recDiv.innerHTML = '<div style="padding: 30px; text-align: center; color: #666;">🔍 AI matching you with top Haryana lawyers...</div>';
            
            fetch(`/cases/${caseId}/recommendations`, {method: 'POST'})
                .then(r => r.json())
                .then(showRecommendations)
                .catch(e => {
                    recDiv.innerHTML = '<div style="color: #dc3545; padding: 20px;">❌ Error loading lawyers. Check server console.</div>';
                });
        }
        
        function showRecommendations(data) {
            const div = document.getElementById('recommendations');
            if (!data.recommendations?.length) {
                div.innerHTML = '<div class="case-card" style="border-left-color: #ffc107;"><p>No lawyers found yet. Database needs seeding.</p></div>';
                return;
            }
            div.innerHTML = data.recommendations.map((r, i) => `
                <div class="lawyer-card">
                    <h4><strong>${r.name}</strong></h4>
                    <p><strong>${r.specialization}</strong> | ${r.city} | ${r.experience_years || 'N/A'} yrs | ⭐${r.rating || 'N/A'}</p>
                    <p><strong>Match Score: ${r.score}/100</strong> <span class="status">AI Recommended</span></p>
                    <button onclick="acceptLawyer(${data.rec_ids[i] || 0})" style="background: #28a745;">✅ Accept Lawyer</button>
                </div>
            `).join('');
        }
        
        function acceptLawyer(recId) {
            fetch(`/recommendations/${recId}/client-accept`, {method: 'POST'})
                .then(r => r.json())
                .then(() => {
                    alert('✅ Lawyer accepted! Visit /lawyer to manage requests.');
                    loadRecommendations(currentCaseId);
                });
        }
        
        function sendMessage() {
            const msg = document.getElementById('message').value.trim();
            if (!msg) return;
            
            const useCtx = document.getElementById('use-context').checked;
            addMessage('You', msg);
            document.getElementById('message').value = '';
            
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg, use_case_context: useCtx})
            })
            .then(r => r.json())
            .then(data => {
                const contextNote = data.used_case_context ? '📁 (Using case context)' : '';
                const docsNote = data.retrieved_count ? `📚 (${data.retrieved_count} docs)` : '';
                addMessage('LexConnect AI', data.answer + '<br><small>' + contextNote + ' ' + docsNote + '<br>⚖️ ' + data.note + '</small>');
            })
            .catch(e => addMessage('Error', 'Chat service unavailable'));
        }
        
        function addMessage(sender, text) {
            const chat = document.getElementById('chat');
            const div = document.createElement('div');
            div.style.marginBottom = '20px';
            div.innerHTML = `<div style="font-weight: 600; color: ${sender === 'You' ? '#1976d2' : '#28a745'}; margin-bottom: 8px;">${sender}</div><div style="line-height: 1.6;">${text}</div>`;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }
        
        // Keyboard shortcuts
        document.getElementById('message').addEventListener('keypress', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        document.getElementById('new-case-text').addEventListener('keypress', e => {
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                createNewCase();
            }
        });
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
const LAWYER_ID = 3;

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


@app.get("/health")
def health() -> Dict:
    return {
        "status": "LexConnect LIVE ✅", 
        "vectors_loaded": 37134,
        "legal_docs": 12378,
        "endpoints": ["/", "/chat", "/cases?client_id=789", "/lawyer"],
        "client_id": 789
    }