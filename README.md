# 🤖 AI Resume Analyzer

An AI-powered web application that analyzes resumes by extracting key information and providing useful insights like resume score and improvement suggestions.

---

## 📌 Features

- 📄 Upload Resume (PDF)
- 📧 Extract Email Address
- 📱 Extract Phone Number
- 🛠 Identify Skills (basic)
- 📊 Resume Score (basic analysis)
- 💡 Suggestions for improvement
- 💬 Talk to Professional (AI-based guidance - optional feature)

---

## 🧠 How It Works

1. User uploads a resume (PDF)
2. Backend processes the file using NLP techniques
3. Extracts structured data:
   - Name
   - Email
   - Phone number
   - Skills
4. Displays results on dashboard
5. Provides analysis & suggestions

---

## 🖥️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript / React  
- **Backend:** FastAPI (Python)  
- **Libraries:** Regex / NLP tools (like spaCy, PyPDF, etc.)

---

## 📷 Screenshots

> Add your UI screenshots here

---

## ⚙️ Installation & Setup

```bash
# Clone the repository
git clone https://github.com/your-username/ai-resume-analyzer.git

# Navigate to project folder
cd ai-resume-analyzer

# Install backend dependencies
pip install -r requirements.txt

# Run the backend server
uvicorn main:app --reload
