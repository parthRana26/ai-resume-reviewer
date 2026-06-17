// Frontend API Controller - AI Resume Reviewer

const BASE_URL = window.location.origin.includes("http") ? window.location.origin : "http://127.0.0.1:8000";

// DOM Selector Elements
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const dropzoneText = document.getElementById("dropzoneText");
const dropzoneIcon = document.getElementById("dropzoneIcon");
const fileInfo = document.getElementById("fileInfo");
const uploadBtn = document.getElementById("uploadBtn");
const uploadAlert = document.getElementById("uploadAlert");

const resumeSelect = document.getElementById("resumeSelect");
const roleInput = document.getElementById("roleInput");
const analyzeBtn = document.getElementById("analyzeBtn");

const emptyState = document.getElementById("emptyState");
const loaderState = document.getElementById("loaderState");
const errorState = document.getElementById("errorState");
const errorMessage = document.getElementById("errorMessage");
const reportContainer = document.getElementById("reportContainer");
const terminalLogs = document.getElementById("terminalLogs");

// Status Tracker Steps
const stepParser = document.getElementById("step-parser");
const stepRag = document.getElementById("step-rag");
const stepAnalyzer = document.getElementById("step-analyzer");
const stepFeedback = document.getElementById("step-feedback");

// Report Elements
const reportRole = document.getElementById("reportRole");
const strengthsList = document.getElementById("strengthsList");
const weaknessesList = document.getElementById("weaknessesList");
const missingSkillsCloud = document.getElementById("missingSkillsCloud");
const recommendationsList = document.getElementById("recommendationsList");
const finalFeedbackText = document.getElementById("finalFeedbackText");
const newScanBtn = document.getElementById("newScanBtn");
const retryBtn = document.getElementById("retryBtn");

let selectedFile = null;
let pollingInterval = null;

// Initial Setup
document.addEventListener("DOMContentLoaded", () => {
    loadResumeDropdown();
    setupDropzone();
    setupEventListeners();
    setupGlowCards();
    setupTabs();
    setupSidebarToggle();
});

// Cursor Tracking Glow Cards Effect
function setupGlowCards() {
    document.addEventListener("mousemove", (e) => {
        const cards = document.querySelectorAll(".glow-card");
        cards.forEach(card => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty("--mouse-x", `${x}px`);
            card.style.setProperty("--mouse-y", `${y}px`);
        });
    });
}

// Tab Switching Mechanics
function setupTabs() {
    const tabs = document.querySelectorAll(".tab-link");
    const sidebar = document.getElementById("reportSidebar");
    const overlay = document.getElementById("sidebarOverlay");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            // Remove active class from all links
            tabs.forEach(t => t.classList.remove("active"));
            // Add active class to clicked link
            tab.classList.add("active");
            
            // Toggle corresponding tab content panel
            const targetTab = tab.getAttribute("data-tab");
            const contents = document.querySelectorAll(".tab-content");
            contents.forEach(content => {
                content.classList.remove("active");
                if (content.id === targetTab) {
                    content.classList.add("active");
                }
            });

            // On mobile viewports, collapse the sidebar and overlay after clicking
            if (sidebar && sidebar.classList.contains("open")) {
                sidebar.classList.remove("open");
            }
            if (overlay && overlay.classList.contains("active")) {
                overlay.classList.remove("active");
            }
        });
    });
}

// Mobile Sidebar Toggle mechanics
function setupSidebarToggle() {
    const toggleBtn = document.getElementById("sidebarToggleBtn");
    const sidebar = document.getElementById("reportSidebar");
    const overlay = document.getElementById("sidebarOverlay");
    
    if (toggleBtn && sidebar && overlay) {
        toggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
            overlay.classList.toggle("active");
        });
        
        overlay.addEventListener("click", () => {
            sidebar.classList.remove("open");
            overlay.classList.remove("active");
        });
    }
}

// Load resumes from database into select dropdown
async function loadResumeDropdown() {
    try {
        const response = await fetch(`${BASE_URL}/resumes`);
        if (!response.ok) throw new Error("Failed to fetch resumes list.");
        
        const resumes = await response.json();
        
        // Save current selected value if any
        const currentSelection = resumeSelect.value;
        
        // Reset option list
        resumeSelect.innerHTML = '<option value="" disabled selected>Select from database...</option>';
        
        resumes.forEach(resume => {
            const opt = document.createElement("option");
            opt.value = resume.id;
            opt.textContent = `${resume.filename} (Uploaded: ${formatDate(resume.uploaded_at)})`;
            resumeSelect.appendChild(opt);
        });

        // Restore selection if still valid
        if (currentSelection && resumes.some(r => r.id === currentSelection)) {
            resumeSelect.value = currentSelection;
        }
        
        validateSetup();
    } catch (err) {
        console.error("Error loading resumes dropdown:", err);
    }
}

// Drag & Drop Setup
function setupDropzone() {
    dropzone.addEventListener("click", () => fileInput.click());
    
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Handle drag events
    ["dragenter", "dragover"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
        }, false);
    });

    dropzone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
}

function handleFileSelect(file) {
    const ext = file.name.split(".").pop().toLowerCase();
    if (ext !== "pdf" && ext !== "docx") {
        showToast("Invalid format! Only PDF and DOCX are allowed.", "error");
        resetDropzone();
        return;
    }
    
    selectedFile = file;
    dropzoneIcon.className = "fa-solid fa-file-circle-check file-icon text-success";
    dropzoneText.innerHTML = `Selected: <strong>${file.name}</strong>`;
    fileInfo.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
    uploadBtn.disabled = false;
}

function resetDropzone() {
    selectedFile = null;
    dropzoneIcon.className = "fa-solid fa-file-pdf file-icon";
    dropzoneText.innerHTML = 'Drag & drop your file here or <span class="browse-btn">Browse</span>';
    fileInfo.textContent = "";
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<i class="fa-solid fa-arrow-up-from-bracket"></i> Upload to Server';
    fileInput.value = "";
}

// Event Listeners Registration
function setupEventListeners() {
    uploadBtn.addEventListener("click", uploadFile);
    resumeSelect.addEventListener("change", validateSetup);
    roleInput.addEventListener("input", validateSetup);
    roleInput.addEventListener("change", validateSetup);
    analyzeBtn.addEventListener("click", triggerAnalysis);
    newScanBtn.addEventListener("click", resetToSearch);
    retryBtn.addEventListener("click", resetToSearch);
}

function validateSetup() {
    analyzeBtn.disabled = !(resumeSelect.value && roleInput.value.trim());
}

// Upload file to FastAPI server
async function uploadFile() {
    if (!selectedFile) return;
    
    const formData = new FormData();
    formData.append("file", selectedFile);
    
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Uploading...';
    
    try {
        const response = await fetch(`${BASE_URL}/upload-resume`, {
            method: "POST",
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "Upload failed.");
        }
        
        showToast(`"${data.filename}" registered successfully!`);
        resetDropzone();
        
        // Refresh dropdown and auto-select new file
        await loadResumeDropdown();
        resumeSelect.value = data.resume_id;
        validateSetup();
        
    } catch (err) {
        console.error("Upload error:", err);
        showToast(err.message || "Failed to upload resume.", "error");
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fa-solid fa-arrow-up-from-bracket"></i> Upload to Server';
    }
}

// Start analysis task
async function triggerAnalysis() {
    const resumeId = resumeSelect.value;
    const jobRole = roleInput.value.trim();
    
    if (!resumeId || !jobRole) return;
    
    // Set UI to loading state
    switchState("loader");
    resetProgressSteps();
    
    try {
        const response = await fetch(`${BASE_URL}/analyze-resume`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ resume_id: resumeId, job_role: jobRole })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "Analysis startup failed.");
        }
        
        const analysisId = data.analysis_id;
        startProgressSimulation(); // Simulated progress updates and terminal logs
        
        // Start polling results
        pollAnalysis(analysisId);
        
    } catch (err) {
        console.error("Analysis trigger error:", err);
        showError(err.message || "Could not launch analysis task.");
    }
}

// Poll analysis status
function pollAnalysis(analysisId) {
    if (pollingInterval) clearInterval(pollingInterval);
    
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`${BASE_URL}/analysis/${analysisId}`);
            if (!response.ok) throw new Error("Failed to fetch analysis status.");
            
            const data = await response.json();
            
            if (data.status === "completed") {
                clearInterval(pollingInterval);
                completeProgressSteps();
                setTimeout(() => {
                    renderReport(data.report);
                    switchState("report");
                    showToast("Analysis report compiled successfully!");
                }, 600);
            } else if (data.status === "failed") {
                clearInterval(pollingInterval);
                showError(data.error || "The AI agent failed to analyze the document.");
            }
            
        } catch (err) {
            console.error("Polling error:", err);
            clearInterval(pollingInterval);
            showError(err.message || "Failed to poll analysis status.");
        }
    }, 2000);
}

// Render report contents to DOM
function renderReport(report) {
    if (!report) return;

    // Show/hide tabs and groups based on backend output data availability
    const toggleElement = (elId, condition) => {
        const el = document.getElementById(elId);
        if (el) el.style.display = condition ? "" : "none";
    };

    // Evaluate each feature's presence in backend report
    const hasGaps = (report.strengths && report.strengths.length > 0) || (report.weaknesses && report.weaknesses.length > 0);
    const hasRecruiter = !!report.recruiter;
    const hasHiring = !!report.hiring_manager;
    const hasSkills = report.missing_skills && report.missing_skills.length > 0;
    const hasRewrite = !!report.rewrite;
    const hasRecommendations = report.recommendations && report.recommendations.length > 0;
    const hasInterview = !!report.interview;
    const hasRoadmap = !!report.roadmap;

    toggleElement("nav-gaps", hasGaps);
    toggleElement("nav-recruiter", hasRecruiter);
    toggleElement("nav-hiring", hasHiring);
    toggleElement("nav-skills", hasSkills);
    toggleElement("nav-rewrite", hasRewrite);
    toggleElement("nav-recommendations", hasRecommendations);
    toggleElement("nav-interview", hasInterview);
    toggleElement("nav-roadmap", hasRoadmap);

    // Hide entire groups if all constituent tabs inside them are hidden
    toggleElement("group-dashboard", true); // Overview is always present
    toggleElement("group-personas", hasRecruiter || hasHiring);
    toggleElement("group-ats", hasSkills || hasRewrite || hasRecommendations);
    toggleElement("group-career", hasInterview || hasRoadmap);

    // Set header role
    reportRole.textContent = report.job_role || "Selected Role";
    
    // Populate simple text elements
    finalFeedbackText.textContent = report.final_feedback || "";
    
    // Populate and animate score circles & count-up numbers
    const overallScore = report.overall_score ?? 0;
    const atsScore = report.ats_score ?? 0;
    const skillsScore = report.skills_score ?? 0;
    const experienceScore = report.experience_score ?? 0;
    const projectScore = report.project_score ?? 0;
    const educationScore = report.education_score ?? 0;

    animateScoreCircle("overall", overallScore, 283);
    animateScoreCircle("ats", atsScore, 220);
    animateScoreCircle("skills", skillsScore, 220);
    animateScoreCircle("experience", experienceScore, 220);
    animateScoreCircle("project", projectScore, 220);
    animateScoreCircle("education", educationScore, 220);
    
    // Populate confidence percentage displays
    const overallConf = report.overall_confidence ?? 0;
    const atsConf = report.ats_confidence ?? 0;
    const skillsConf = report.skills_confidence ?? 0;
    const experienceConf = report.experience_confidence ?? 0;
    const projectConf = report.project_confidence ?? 0;
    const educationConf = report.education_confidence ?? 0;

    document.getElementById("conf-overall").textContent = `Confidence: ${Math.round(overallConf * 100)}%`;
    document.getElementById("conf-ats").textContent = `Confidence: ${Math.round(atsConf * 100)}%`;
    document.getElementById("conf-skills").textContent = `Confidence: ${Math.round(skillsConf * 100)}%`;
    document.getElementById("conf-experience").textContent = `Confidence: ${Math.round(experienceConf * 100)}%`;
    document.getElementById("conf-project").textContent = `Confidence: ${Math.round(projectConf * 100)}%`;
    document.getElementById("conf-education").textContent = `Confidence: ${Math.round(educationConf * 100)}%`;
    
    // Render score explanations section dynamically
    const explanationsList = document.getElementById("explanationsList");
    explanationsList.innerHTML = '<h4 style="font-size: 1.1rem; font-weight:600; margin-bottom:1.25rem;"><i class="fa-solid fa-file-invoice" style="color:var(--secondary);"></i> Recruiter Evaluation Details</h4>';
    const categories = [
        { name: "Overall Compatibility", score: overallScore, confidence: overallConf, explanation: report.overall_explanation || "No explanation provided." },
        { name: "ATS Scan Index", score: atsScore, confidence: atsConf, explanation: report.ats_explanation || "No explanation provided." },
        { name: "Technical Skills Alignment", score: skillsScore, confidence: skillsConf, explanation: report.skills_explanation || "No explanation provided." },
        { name: "Professional Experience Fit", score: experienceScore, confidence: experienceConf, explanation: report.experience_explanation || "No explanation provided." },
        { name: "Projects Scope Audit", score: projectScore, confidence: projectConf, explanation: report.project_explanation || "No explanation provided." },
        { name: "Academic Credentials Fit", score: educationScore, confidence: educationConf, explanation: report.education_explanation || "No explanation provided." }
    ];
    categories.forEach(cat => {
        const item = document.createElement("div");
        item.className = "explanation-item";
        item.innerHTML = `
            <div class="explanation-title-wrap">
                <span class="explanation-title">${cat.name}</span>
                <span class="explanation-metrics">Score: ${cat.score}% | Confidence: ${Math.round(cat.confidence * 100)}%</span>
            </div>
            <p class="explanation-text">${cat.explanation}</p>
        `;
        explanationsList.appendChild(item);
    });

    // Reset tabs selection to default overview
    const tabs = document.querySelectorAll(".tab-link");
    tabs.forEach(t => t.classList.remove("active"));
    const defaultTab = document.querySelector('[data-tab="tab-overview"]');
    if (defaultTab) defaultTab.classList.add("active");
    
    const contents = document.querySelectorAll(".tab-content");
    contents.forEach(c => c.classList.remove("active"));
    const defaultContent = document.getElementById("tab-overview");
    if (defaultContent) defaultContent.classList.add("active");
    
    // Populate Strengths list
    strengthsList.innerHTML = "";
    if (Array.isArray(report.strengths)) {
        report.strengths.forEach(strength => {
            const li = document.createElement("li");
            li.textContent = strength;
            strengthsList.appendChild(li);
        });
    }
    
    // Populate Weaknesses list
    weaknessesList.innerHTML = "";
    if (Array.isArray(report.weaknesses)) {
        report.weaknesses.forEach(weakness => {
            const li = document.createElement("li");
            li.textContent = weakness;
            weaknessesList.appendChild(li);
        });
    }
    
    // Populate Missing Skills cloud
    missingSkillsCloud.innerHTML = "";
    if (!report.missing_skills || !Array.isArray(report.missing_skills) || report.missing_skills.length === 0) {
        missingSkillsCloud.innerHTML = '<p class="text-dim">No major skill gaps identified.</p>';
    } else {
        report.missing_skills.forEach(skill => {
            const span = document.createElement("span");
            span.className = "tag-badge";
            span.textContent = skill;
            missingSkillsCloud.appendChild(span);
        });
    }
    
    // Populate Recommendations lists
    recommendationsList.innerHTML = "";
    if (!report.recommendations || !Array.isArray(report.recommendations) || report.recommendations.length === 0) {
        recommendationsList.innerHTML = '<p class="text-dim">No specific recommendations needed.</p>';
    } else {
        report.recommendations.forEach((rec, idx) => {
            const recItem = document.createElement("div");
            recItem.className = `rec-item ${idx === 0 ? 'open' : ''}`;
            
            const whyItMattersText = rec.why_it_matter || rec.why_it_matters || "No context provided.";
            const improvementText = rec.improvement || "No optimization suggested.";
            const exampleContentText = rec.example_content || "No sample phrasing provided.";

            recItem.innerHTML = `
                <div class="rec-header">
                    <div class="rec-title-wrap">
                        <i class="fa-solid fa-lightbulb"></i>
                        <span class="rec-title">${rec.issue || "Opportunity"}</span>
                    </div>
                    <i class="fa-solid fa-chevron-down rec-chevron"></i>
                </div>
                <div class="rec-content">
                    <div class="rec-meta">
                        <span>Why It Matters</span>
                        <p>${whyItMattersText}</p>
                    </div>
                    <div class="rec-meta">
                        <span>Actionable Fix</span>
                        <p>${improvementText}</p>
                    </div>
                    <div class="rec-example-box">
                        <div class="rec-example-header">
                            <span>Recommended Phrasing</span>
                            <button class="btn-copy" onclick="copyExampleText(this)">
                                <i class="fa-regular fa-copy"></i> Copy
                            </button>
                        </div>
                        <div class="rec-example-body">${exampleContentText}</div>
                    </div>
                </div>
            `;
            
            // Accordion toggle click action
            recItem.querySelector(".rec-header").addEventListener("click", () => {
                recItem.classList.toggle("open");
            });
            
            recommendationsList.appendChild(recItem);
        });
    }

    // ----------------- Populate Recruiter Tab -----------------
    if (report.recruiter) {
        const decisionBadge = document.getElementById("recruiterDecisionBadge");
        if (report.recruiter.shortlist_decision) {
            decisionBadge.className = "badge-item text-success";
            decisionBadge.style.background = "rgba(16, 185, 129, 0.1)";
            decisionBadge.style.borderColor = "rgba(16, 185, 129, 0.2)";
            decisionBadge.innerHTML = '<i class="fa-solid fa-circle-check"></i> Shortlist: YES';
        } else {
            decisionBadge.className = "badge-item text-danger";
            decisionBadge.style.background = "rgba(239, 68, 68, 0.1)";
            decisionBadge.style.borderColor = "rgba(239, 68, 68, 0.2)";
            decisionBadge.innerHTML = '<i class="fa-solid fa-circle-xmark"></i> Shortlist: NO';
        }

        const riskBadge = document.getElementById("recruiterRiskBadge");
        const risk = (report.recruiter.hiring_risk_level || "medium").toLowerCase();
        if (risk === "low") {
            riskBadge.className = "badge-item text-success";
            riskBadge.style.background = "rgba(16, 185, 129, 0.1)";
            riskBadge.style.borderColor = "rgba(16, 185, 129, 0.2)";
            riskBadge.innerHTML = '<i class="fa-solid fa-shield-halved"></i> Risk: LOW';
        } else if (risk === "medium") {
            riskBadge.className = "badge-item text-warning";
            riskBadge.style.background = "rgba(245, 158, 11, 0.1)";
            riskBadge.style.borderColor = "rgba(245, 158, 11, 0.2)";
            riskBadge.innerHTML = '<i class="fa-solid fa-shield-halved"></i> Risk: MEDIUM';
        } else {
            riskBadge.className = "badge-item text-danger";
            riskBadge.style.background = "rgba(239, 68, 68, 0.1)";
            riskBadge.style.borderColor = "rgba(239, 68, 68, 0.2)";
            riskBadge.innerHTML = '<i class="fa-solid fa-shield-halved"></i> Risk: HIGH';
        }

        document.getElementById("recruiterModelText").textContent = report.recruiter.model_used || "Unknown Model";
        document.getElementById("recruiterSummaryText").textContent = report.recruiter.recruiter_summary || "No recruiter summary provided.";

        const recStrengths = document.getElementById("recruiterStrengthsList");
        recStrengths.innerHTML = "";
        if (Array.isArray(report.recruiter.strengths)) {
            report.recruiter.strengths.forEach(s => {
                const li = document.createElement("li");
                li.textContent = s;
                recStrengths.appendChild(li);
            });
        }

        const recWeaknesses = document.getElementById("recruiterWeaknessesList");
        recWeaknesses.innerHTML = "";
        if (Array.isArray(report.recruiter.weaknesses)) {
            report.recruiter.weaknesses.forEach(w => {
                const li = document.createElement("li");
                li.textContent = w;
                recWeaknesses.appendChild(li);
            });
        }
    }

    // ----------------- Populate Hiring Manager Tab -----------------
    if (report.hiring_manager) {
        const hmRecBadge = document.getElementById("hiringRecommendationBadge");
        const recText = report.hiring_manager.interview_recommendation || "No recommendation provided.";
        if (recText.toLowerCase().includes("strong recommend") || recText.toLowerCase().includes("recommend")) {
            hmRecBadge.className = "badge-item text-success";
            hmRecBadge.style.background = "rgba(16, 185, 129, 0.1)";
            hmRecBadge.style.borderColor = "rgba(16, 185, 129, 0.2)";
            hmRecBadge.innerHTML = '<i class="fa-solid fa-circle-check"></i> ' + recText;
        } else if (recText.toLowerCase().includes("reservations") || recText.toLowerCase().includes("medium")) {
            hmRecBadge.className = "badge-item text-warning";
            hmRecBadge.style.background = "rgba(245, 158, 11, 0.1)";
            hmRecBadge.style.borderColor = "rgba(245, 158, 11, 0.2)";
            hmRecBadge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> ' + recText;
        } else {
            hmRecBadge.className = "badge-item text-danger";
            hmRecBadge.style.background = "rgba(239, 68, 68, 0.1)";
            hmRecBadge.style.borderColor = "rgba(239, 68, 68, 0.2)";
            hmRecBadge.innerHTML = '<i class="fa-solid fa-circle-xmark"></i> ' + recText;
        }

        document.getElementById("hiringModelText").textContent = report.hiring_manager.model_used || "Unknown Model";
        document.getElementById("hiringSkillDepthText").textContent = report.hiring_manager.skill_depth_assessment || "No assessment provided.";
        document.getElementById("hiringProjectQualityText").textContent = report.hiring_manager.project_quality_review || "No project quality review provided.";

        const hmConcerns = document.getElementById("hiringConcernsList");
        hmConcerns.innerHTML = "";
        if (Array.isArray(report.hiring_manager.technical_concerns)) {
            report.hiring_manager.technical_concerns.forEach(c => {
                const li = document.createElement("li");
                li.textContent = c;
                hmConcerns.appendChild(li);
            });
        }
    }

    // ----------------- Populate Resume Rewrite Tab -----------------
    if (report.rewrite) {
        const bulletsList = document.getElementById("rewriteBulletsList");
        bulletsList.innerHTML = "";
        if (Array.isArray(report.rewrite.optimized_bullets)) {
            report.rewrite.optimized_bullets.forEach(b => {
                const div = document.createElement("div");
                div.className = "rewrite-item-card";
                div.style.cssText = "background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.85rem 1rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem;";
                div.innerHTML = `
                    <p style="font-size: 0.9rem; color: var(--text-main); margin: 0; line-height:1.5;">${b}</p>
                    <button class="btn-copy" onclick="navigator.clipboard.writeText('${b.replace(/'/g, "\\'")}'); showToast('Copied phrasing!');" style="background:none; border:none; color:var(--secondary); cursor:pointer; font-size:0.85rem; display:flex; align-items:center; gap:0.25rem; white-space:nowrap;">
                        <i class="fa-regular fa-copy"></i> Copy
                    </button>
                `;
                bulletsList.appendChild(div);
            });
        }

        const rewriteProjects = document.getElementById("rewriteProjectsList");
        rewriteProjects.innerHTML = "";
        if (Array.isArray(report.rewrite.rewritten_projects)) {
            report.rewrite.rewritten_projects.forEach(p => {
                if (p) {
                    const div = document.createElement("div");
                    div.className = "rewrite-item-card";
                    div.style.cssText = "background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.85rem 1rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem;";
                    div.innerHTML = `
                        <p style="font-size: 0.9rem; color: var(--text-main); margin: 0; line-height:1.5;">${p}</p>
                        <button class="btn-copy" onclick="navigator.clipboard.writeText('${p.replace(/'/g, "\\'")}'); showToast('Copied phrasing!');" style="background:none; border:none; color:var(--secondary); cursor:pointer; font-size:0.85rem; display:flex; align-items:center; gap:0.25rem; white-space:nowrap;">
                            <i class="fa-regular fa-copy"></i> Copy
                        </button>
                    `;
                    rewriteProjects.appendChild(div);
                }
            });
        }
    }

    // ----------------- Populate Interview Tab -----------------
    if (report.interview) {
        const buildQuestionList = (elementId, questions) => {
            const list = document.getElementById(elementId);
            list.innerHTML = "";
            if (Array.isArray(questions)) {
                questions.forEach((q, idx) => {
                    const div = document.createElement("div");
                    div.className = "question-card";
                    div.style.cssText = "background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.85rem 1rem; display: flex; gap: 0.75rem; align-items: flex-start;";
                    div.innerHTML = `
                        <span style="color:var(--secondary); font-weight:700; font-size: 0.9rem;">Q${idx+1}:</span>
                        <p style="font-size: 0.9rem; color: var(--text-main); margin: 0; line-height:1.5;">${q}</p>
                    `;
                    list.appendChild(div);
                });
            }
        };

        buildQuestionList("interviewTechnicalList", report.interview.technical_questions);
        buildQuestionList("interviewProjectsList", report.interview.project_based_questions);
        buildQuestionList("interviewHRList", report.interview.hr_questions);
    }

    // ----------------- Populate Roadmap Tab -----------------
    if (report.roadmap) {
        document.getElementById("roadmapCurrentLevelText").textContent = report.roadmap.current_level || "N/A";
        document.getElementById("roadmapTargetRoleText").textContent = report.roadmap.next_target_role || "N/A";

        const buildRoadmapList = (elementId, steps) => {
            const list = document.getElementById(elementId);
            list.innerHTML = "";
            if (Array.isArray(steps)) {
                steps.forEach(step => {
                    const li = document.createElement("li");
                    li.style.cssText = "font-size: 0.9rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 0.5rem;";
                    li.textContent = step;
                    list.appendChild(li);
                });
            }
        };

        buildRoadmapList("roadmap30dList", report.roadmap.roadmap_30d);
        buildRoadmapList("roadmap90dList", report.roadmap.roadmap_90d);
        buildRoadmapList("roadmap6mList", report.roadmap.roadmap_6m);
    }
}

// Animate Circular Progress Meter SVG Offset & Numerical Count-Up
function animateScoreCircle(elementId, score, circumference) {
    const textVal = document.getElementById(`val-${elementId}`);
    const svgCircle = document.getElementById(`svg-${elementId}`);
    
    // Animate Circular Stroke
    const offset = circumference - (circumference * score) / 100;
    setTimeout(() => {
        svgCircle.style.strokeDashoffset = offset;
    }, 100);
    
    // Animate Numerical Value Count-up
    let current = 0;
    const duration = 1200; // 1.2s total animation
    const stepTime = Math.max(Math.floor(duration / (score || 1)), 15);
    
    const timer = setInterval(() => {
        if (score === 0) {
            textVal.textContent = "0%";
            clearInterval(timer);
            return;
        }
        current += 1;
        textVal.textContent = `${current}%`;
        if (current >= score) {
            textVal.textContent = `${score}%`;
            clearInterval(timer);
        }
    }, stepTime);
}

// Clipboard copying utility
window.copyExampleText = function(button) {
    const codeBlock = button.closest(".rec-example-box").querySelector(".rec-example-body");
    navigator.clipboard.writeText(codeBlock.textContent.trim()).then(() => {
        button.innerHTML = '<i class="fa-solid fa-check text-success"></i> Copied!';
        showToast("Example content copied to clipboard!");
        setTimeout(() => {
            button.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
        }, 2000);
    }).catch(err => {
        console.error("Clipboard copy failed:", err);
    });
};

// Toast Notification Manager
function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let icon = "fa-circle-check";
    if (type === "error") icon = "fa-circle-exclamation";
    else if (type === "info") icon = "fa-circle-info";
    
    toast.innerHTML = `
        <i class="fa-solid ${icon} toast-icon"></i>
        <span class="toast-message">${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Remove toast slide out
    setTimeout(() => {
        toast.style.animation = "toastSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards";
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3500);
}

// UI Toggling helpers
// States: "empty", "loader", "error", "report"
function switchState(state) {
    emptyState.style.display = "none";
    loaderState.style.display = "none";
    errorState.style.display = "none";
    reportContainer.style.display = "none";
    
    if (state === "empty") emptyState.style.display = "flex";
    else if (state === "loader") loaderState.style.display = "flex";
    else if (state === "error") errorState.style.display = "flex";
    else if (state === "report") reportContainer.style.display = "block";
}

function resetToSearch() {
    switchState("empty");
    if (pollingInterval) clearInterval(pollingInterval);
    loadResumeDropdown();
}

function showError(msg) {
    errorMessage.textContent = msg;
    switchState("error");
    if (pollingInterval) clearInterval(pollingInterval);
    showToast("Resume analysis workflow encountered a failure.", "error");
}

// Loader Simulation Timers & Log Feeds
let simulationTimers = [];

function resetProgressSteps() {
    simulationTimers.forEach(clearTimeout);
    simulationTimers = [];
    
    stepParser.className = "status-step active";
    stepParser.querySelector("i").className = "fa-solid fa-circle-notch fa-spin";
    
    [stepRag, stepAnalyzer, stepFeedback].forEach(step => {
        step.className = "status-step";
        step.querySelector("i").className = "fa-solid fa-circle";
    });
    
    terminalLogs.textContent = "Bootstrapping Multi-Agent execution environment...";
}

function startProgressSimulation() {
    // Stage 1 logs (Parser)
    simulationTimers.push(setTimeout(() => {
        terminalLogs.textContent = "Parsing document text layout parameters...";
    }, 1200));
    
    simulationTimers.push(setTimeout(() => {
        terminalLogs.textContent = "Groq Llama 3.3 parsing structured experience and academic matrices...";
    }, 2400));
    
    // Transition to RAG Indexer
    simulationTimers.push(setTimeout(() => {
        setStepComplete(stepParser);
        setStepActive(stepRag);
        terminalLogs.textContent = "Splitting raw text layers into indexable chunks...";
    }, 3800));
    
    simulationTimers.push(setTimeout(() => {
        terminalLogs.textContent = "Generating local vector arrays using HuggingFaceEmbeddings...";
    }, 5000));
    
    simulationTimers.push(setTimeout(() => {
        terminalLogs.textContent = "Writing chunks to local ChromaDB collections...";
    }, 6200));

    // Transition to Analyzer
    simulationTimers.push(setTimeout(() => {
        setStepComplete(stepRag);
        setStepActive(stepAnalyzer);
        terminalLogs.textContent = "Querying ChromaDB for role-related metadata...";
    }, 7800));

    simulationTimers.push(setTimeout(() => {
        terminalLogs.textContent = "Evaluating skills matching metrics & project relevancy indices...";
    }, 9200));

    // Transition to Feedback Compiler
    simulationTimers.push(setTimeout(() => {
        setStepComplete(stepAnalyzer);
        setStepActive(stepFeedback);
        terminalLogs.textContent = "Compiling missing technologies checklist...";
    }, 11200));

    simulationTimers.push(setTimeout(() => {
        terminalLogs.textContent = "Formatting actionable phrasing recommendation structures...";
    }, 12800));

    simulationTimers.push(setTimeout(() => {
        terminalLogs.textContent = "Assembling finalized report details...";
    }, 14000));
}

function completeProgressSteps() {
    simulationTimers.forEach(clearTimeout);
    setStepComplete(stepParser);
    setStepComplete(stepRag);
    setStepComplete(stepAnalyzer);
    setStepComplete(stepFeedback);
    terminalLogs.textContent = "Report compiled successfully.";
}

function setStepActive(element) {
    element.className = "status-step active";
    element.querySelector("i").className = "fa-solid fa-circle-notch fa-spin";
}

function setStepComplete(element) {
    element.className = "status-step complete";
    element.querySelector("i").className = "fa-solid fa-circle-check text-success";
}

// Helpers
function formatDate(isoString) {
    if (!isoString) return "";
    const date = new Date(isoString.replace(" ", "T")); // SQLite raw text fallback
    return date.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}
