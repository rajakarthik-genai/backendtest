/**
 * Mock API for Digital Twin Health Dashboard
 * This file provides mock data for testing the dashboard without a backend
 * To use: Include this script before app.js in your HTML
 */

// Mock data for different body regions and years
const mockHealthData = {
  regions: {
    shoulder: {
      condition: "Rotator Cuff Tear",
      severity: "Moderate",
      year: 2023,
      symptoms: [
        "Shoulder pain during movement",
        "Limited range of motion",
        "Weakness in arm lifting",
        "Night pain when lying on affected side"
      ],
      treatments: [
        "Physical therapy sessions",
        "Anti-inflammatory medication",
        "Rest and activity modification",
        "Ice therapy application"
      ],
      notes: "Patient showing good response to conservative treatment. Continue PT for 6 more weeks.",
      progress: 65
    },
    lungs: {
      condition: "Mild Asthma",
      severity: "Mild",
      year: 2024,
      symptoms: [
        "Occasional wheezing",
        "Shortness of breath during exercise",
        "Mild chest tightness",
        "Dry cough at night"
      ],
      treatments: [
        "Rescue inhaler (albuterol)",
        "Environmental allergen control",
        "Regular exercise routine",
        "Peak flow monitoring"
      ],
      notes: "Well-controlled asthma. Continue current medication regimen.",
      progress: 85
    },
    heart: {
      condition: "Hypertension",
      severity: "Moderate",
      year: 2023,
      symptoms: [
        "Elevated blood pressure readings",
        "Occasional headaches",
        "Mild fatigue",
        "Dizziness when standing"
      ],
      treatments: [
        "ACE inhibitor medication",
        "Low sodium diet",
        "Regular cardiovascular exercise",
        "Daily blood pressure monitoring"
      ],
      notes: "Blood pressure trending downward with lifestyle modifications.",
      progress: 70
    },
    liver: {
      condition: "Fatty Liver",
      severity: "Mild",
      year: 2022,
      symptoms: [
        "Elevated liver enzymes",
        "Mild abdominal discomfort",
        "Fatigue after meals",
        "Occasional nausea"
      ],
      treatments: [
        "Weight reduction program",
        "Mediterranean diet",
        "Regular exercise routine",
        "Alcohol cessation"
      ],
      notes: "Liver function improving with lifestyle changes. Continue current plan.",
      progress: 80
    },
    kidneys: {
      condition: "Kidney Stones",
      severity: "Moderate",
      year: 2023,
      symptoms: [
        "Sharp flank pain",
        "Blood in urine",
        "Frequent urination",
        "Nausea and vomiting"
      ],
      treatments: [
        "Increased fluid intake",
        "Pain management medication",
        "Dietary modifications",
        "Lithotripsy procedure"
      ],
      notes: "Stone successfully passed. Preventive measures in place.",
      progress: 90
    },
    stomach: {
      condition: "GERD",
      severity: "Mild",
      year: 2024,
      symptoms: [
        "Heartburn after meals",
        "Acid regurgitation",
        "Difficulty swallowing",
        "Chronic cough"
      ],
      treatments: [
        "Proton pump inhibitor",
        "Dietary modifications",
        "Elevated head sleeping",
        "Weight management"
      ],
      notes: "Symptoms well-controlled with medication and lifestyle changes.",
      progress: 75
    }
  },
  years: {
    2019: {
      condition: "Migraine",
      severity: "Severe",
      year: 2019,
      symptoms: [
        "Severe throbbing headache",
        "Nausea and vomiting",
        "Light sensitivity",
        "Sound sensitivity",
        "Visual aura"
      ],
      treatments: [
        "Triptan medication",
        "Preventive medication",
        "Stress management techniques",
        "Regular sleep schedule",
        "Trigger identification"
      ],
      notes: "Chronic migraines managed with combination therapy.",
      progress: 60
    },
    2020: {
      condition: "Anxiety Disorder",
      severity: "Moderate",
      year: 2020,
      symptoms: [
        "Persistent worry",
        "Racing heart",
        "Sleep disturbances",
        "Muscle tension",
        "Difficulty concentrating"
      ],
      treatments: [
        "Cognitive behavioral therapy",
        "Mindfulness meditation",
        "Regular exercise",
        "Anti-anxiety medication",
        "Support group participation"
      ],
      notes: "Significant improvement with therapy and medication.",
      progress: 75
    },
    2021: {
      condition: "Lower Back Pain",
      severity: "Moderate",
      year: 2021,
      symptoms: [
        "Chronic lower back pain",
        "Stiffness in morning",
        "Pain radiating to legs",
        "Muscle spasms"
      ],
      treatments: [
        "Physical therapy",
        "Core strengthening exercises",
        "Heat and cold therapy",
        "Ergonomic workplace setup",
        "NSAIDs as needed"
      ],
      notes: "Back pain significantly improved with physical therapy.",
      progress: 80
    },
    2022: {
      condition: "Type 2 Diabetes",
      severity: "Mild",
      year: 2022,
      symptoms: [
        "Elevated blood glucose",
        "Increased thirst",
        "Frequent urination",
        "Fatigue",
        "Blurred vision"
      ],
      treatments: [
        "Metformin medication",
        "Carbohydrate counting",
        "Regular glucose monitoring",
        "Exercise program",
        "Nutritionist consultation"
      ],
      notes: "Blood sugar well-controlled with medication and diet.",
      progress: 85
    },
    2023: {
      condition: "Seasonal Allergies",
      severity: "Mild",
      year: 2023,
      symptoms: [
        "Sneezing",
        "Runny nose",
        "Itchy eyes",
        "Nasal congestion",
        "Postnasal drip"
      ],
      treatments: [
        "Antihistamine medication",
        "Nasal corticosteroid spray",
        "Air purifier use",
        "Pollen avoidance",
        "Immunotherapy consideration"
      ],
      notes: "Seasonal symptoms well-managed with current treatment plan.",
      progress: 90
    },
    2024: {
      condition: "Sleep Apnea",
      severity: "Moderate",
      year: 2024,
      symptoms: [
        "Loud snoring",
        "Gasping during sleep",
        "Daytime fatigue",
        "Morning headaches",
        "Difficulty concentrating"
      ],
      treatments: [
        "CPAP therapy",
        "Weight loss program",
        "Sleep position training",
        "Oral appliance",
        "Regular sleep study monitoring"
      ],
      notes: "Good compliance with CPAP therapy. Sleep quality improving.",
      progress: 70
    }
  }
};

// Mock search results
const mockSearchResults = {
  "headache": [
    { type: "condition", name: "Migraine", year: 2019, region: "head" },
    { type: "symptom", name: "Morning headaches", year: 2024, region: "head" }
  ],
  "pain": [
    { type: "symptom", name: "Shoulder pain", year: 2023, region: "shoulder" },
    { type: "symptom", name: "Lower back pain", year: 2021, region: "back" },
    { type: "symptom", name: "Sharp flank pain", year: 2023, region: "kidneys" }
  ],
  "breathing": [
    { type: "symptom", name: "Shortness of breath", year: 2024, region: "lungs" },
    { type: "symptom", name: "Wheezing", year: 2024, region: "lungs" }
  ]
};

// Override fetch function to return mock data
const originalFetch = window.fetch;

window.fetch = function(url, options) {
  // Check if this is an API call to our health endpoints
  if (url.includes('/api/health/')) {
    return new Promise((resolve) => {
      // Simulate network delay
      setTimeout(() => {
        let mockResponse;
        
        if (url.includes('/region/')) {
          const region = url.split('/region/')[1].split('?')[0];
          mockResponse = mockHealthData.regions[region];
        } else if (url.includes('/history/')) {
          const year = url.split('/history/')[1].split('?')[0];
          mockResponse = mockHealthData.years[year];
        } else if (url.includes('/search')) {
          const searchQuery = new URL(url).searchParams.get('q')?.toLowerCase();
          mockResponse = mockSearchResults[searchQuery] || [];
        } else if (url.includes('/export')) {
          // Mock PDF export
          const pdfContent = new Blob(['Mock PDF content'], { type: 'application/pdf' });
          resolve({
            ok: true,
            blob: () => Promise.resolve(pdfContent)
          });
          return;
        }
        
        if (mockResponse) {
          resolve({
            ok: true,
            json: () => Promise.resolve(mockResponse),
            status: 200
          });
        } else {
          resolve({
            ok: false,
            status: 404,
            json: () => Promise.resolve({ error: 'Not found' })
          });
        }
      }, Math.random() * 500 + 200); // Random delay between 200-700ms
    });
  }
  
  // For non-API calls, use the original fetch
  return originalFetch.apply(this, arguments);
};

// Add some visual feedback for mock mode
document.addEventListener('DOMContentLoaded', () => {
  // Add a small indicator that we're in mock mode
  const mockIndicator = document.createElement('div');
  mockIndicator.innerHTML = `
    <div style="
      position: fixed;
      top: 10px;
      left: 10px;
      background: rgba(255, 193, 7, 0.9);
      color: #000;
      padding: 5px 10px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: bold;
      z-index: 1000;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    ">
      🧪 MOCK MODE
    </div>
  `;
  document.body.appendChild(mockIndicator);
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    mockIndicator.style.opacity = '0.3';
  }, 3000);
  
  console.log('🧪 Mock API loaded successfully!');
  console.log('Available regions:', Object.keys(mockHealthData.regions));
  console.log('Available years:', Object.keys(mockHealthData.years));
});

// Timeline data for regions
const mockTimelineData = {
  head: [
    { date: '2024-06-15', summary: 'Routine neurological checkup - all normal', severity: 'normal' },
    { date: '2024-03-10', summary: 'Mild headache reported, stress-related', severity: 'mild' },
    { date: '2023-11-20', summary: 'Annual brain MRI scan - no abnormalities', severity: 'normal' },
    { date: '2023-08-05', summary: 'Consultation for sleep disorders', severity: 'moderate' }
  ],
  heart: [
    { date: '2024-07-01', summary: 'Cardiovascular health assessment - excellent', severity: 'normal' },
    { date: '2024-04-15', summary: 'Blood pressure monitoring - slightly elevated', severity: 'mild' },
    { date: '2024-01-30', summary: 'Cholesterol levels check - within normal range', severity: 'normal' },
    { date: '2023-10-12', summary: 'ECG performed - normal sinus rhythm', severity: 'normal' }
  ],
  lungs: [
    { date: '2024-06-20', summary: 'Respiratory function test - normal capacity', severity: 'normal' },
    { date: '2024-02-28', summary: 'Chest X-ray for persistent cough', severity: 'mild' },
    { date: '2023-12-15', summary: 'Annual lung function assessment', severity: 'normal' },
    { date: '2023-09-08', summary: 'Bronchitis treatment completed successfully', severity: 'moderate' }
  ],
  liver: [
    { date: '2024-05-25', summary: 'Liver enzyme levels - all within normal range', severity: 'normal' },
    { date: '2024-02-14', summary: 'Hepatitis B vaccination booster', severity: 'normal' },
    { date: '2023-11-30', summary: 'Alcohol consumption counseling session', severity: 'mild' },
    { date: '2023-08-18', summary: 'Liver ultrasound - no abnormalities detected', severity: 'normal' }
  ],
  kidneys: [
    { date: '2024-06-10', summary: 'Kidney function test - excellent results', severity: 'normal' },
    { date: '2024-03-25', summary: 'Urinalysis completed - no issues found', severity: 'normal' },
    { date: '2024-01-12', summary: 'Hydration counseling and lifestyle advice', severity: 'normal' },
    { date: '2023-10-05', summary: 'Kidney stone prevention consultation', severity: 'mild' }
  ],
  stomach: [
    { date: '2024-06-30', summary: 'Digestive health checkup - all systems normal', severity: 'normal' },
    { date: '2024-04-08', summary: 'Treatment for acid reflux - symptoms resolved', severity: 'mild' },
    { date: '2024-01-22', summary: 'Dietary consultation for IBS management', severity: 'moderate' },
    { date: '2023-11-14', summary: 'Colonoscopy screening - no abnormalities', severity: 'normal' }
  ],
  shoulder: [
    { date: '2024-07-05', summary: 'Physical therapy session - improved mobility', severity: 'normal' },
    { date: '2024-04-20', summary: 'Shoulder pain management - cortisone injection', severity: 'moderate' },
    { date: '2024-02-10', summary: 'Rotator cuff assessment - minor strain detected', severity: 'mild' },
    { date: '2023-12-01', summary: 'Shoulder X-ray - no structural damage', severity: 'normal' }
  ]
};

// Mock chat responses
const mockChatResponses = {
  normal: {
    "pain": "Based on your health profile, I can provide some general guidance about pain management. For specific medical advice, please consult with Dr. Ericsson.",
    "medication": "Your current medication regimen appears to be working well. Any changes should be discussed with your healthcare provider.",
    "symptoms": "I can help you understand your symptoms. Please describe what you're experiencing and I'll provide general information.",
    "default": "Thank you for your question. Based on your health profile, I can provide some general guidance. For specific medical advice, please consult with Dr. Ericsson."
  },
  expert: {
    "pain": {
      answer: "Based on comprehensive analysis of your health data and current medical literature, chronic pain management requires a multi-modal approach [1][2]. Your recent assessments indicate musculoskeletal involvement with inflammatory markers within normal range [3]. Evidence suggests combination therapy yields optimal outcomes [4].",
      sources: [
        { id: 1, title: "Chronic Pain Management Guidelines 2024", url: "https://painmanagement.org/guidelines" },
        { id: 2, title: "Multimodal Pain Therapy: A Systematic Review", url: "https://pubmed.ncbi.nlm.nih.gov/pain2024" },
        { id: 3, title: "Patient Lab Results Analysis - Inflammatory Markers", url: "https://example.com/lab-analysis" },
        { id: 4, title: "Evidence-Based Pain Treatment Protocols", url: "https://clinical-evidence.org/pain" }
      ],
      steps: "Analyzed patient history, consulted pain management databases, reviewed recent clinical studies, cross-referenced with current treatment protocols."
    },
    "medication": {
      answer: "Comprehensive medication review reveals good adherence patterns with optimal therapeutic levels achieved [1]. Current regimen aligns with latest clinical guidelines for your condition profile [2]. Drug interaction analysis shows no contraindications [3].",
      sources: [
        { id: 1, title: "Pharmacokinetic Analysis Report", url: "https://example.com/pharm-analysis" },
        { id: 2, title: "Clinical Practice Guidelines - Medication Management", url: "https://guidelines.org/medication" },
        { id: 3, title: "Drug Interaction Database Analysis", url: "https://druginteractions.org/analysis" }
      ],
      steps: "Reviewed medication history, analyzed therapeutic levels, consulted drug databases, verified against clinical guidelines."
    },
    "default": {
      answer: "Based on comprehensive analysis of your health data and current medical literature, I've gathered insights from multiple authoritative sources [1][2]. This research-backed response incorporates the latest clinical evidence and your personal health profile [3].",
      sources: [
        { id: 1, title: "Clinical Guidelines for Patient Care 2024", url: "https://example.com/guidelines" },
        { id: 2, title: "Recent Medical Research on Related Conditions", url: "https://example.com/research" },
        { id: 3, title: "Patient Health Data Analysis Report", url: "https://example.com/analysis" }
      ],
      steps: "Analyzed patient history, consulted medical databases, reviewed recent studies, cross-referenced with clinical guidelines."
    }
  }
};

// Mock API implementation
window.mockAPI = {
  // ...existing methods...

  // New timeline endpoint
  async getTimeline(region) {
    await this.simulateDelay();
    const events = mockTimelineData[region] || [];
    return {
      region: region,
      events: events
    };
  },

  // New chat endpoint
  async sendChatMessage(message, isExpertMode = false) {
    await this.simulateDelay();
    
    if (isExpertMode) {
      // Expert mode response with sources
      const messageType = this.getChatMessageType(message);
      return mockChatResponses.expert[messageType] || mockChatResponses.expert.default;
    } else {
      // Normal mode response
      const messageType = this.getChatMessageType(message);
      return {
        answer: mockChatResponses.normal[messageType] || mockChatResponses.normal.default
      };
    }
  },

  getChatMessageType(message) {
    const lowerMessage = message.toLowerCase();
    if (lowerMessage.includes('pain') || lowerMessage.includes('hurt') || lowerMessage.includes('ache')) {
      return 'pain';
    }
    if (lowerMessage.includes('medication') || lowerMessage.includes('drug') || lowerMessage.includes('pill')) {
      return 'medication';
    }
    if (lowerMessage.includes('symptom') || lowerMessage.includes('feel') || lowerMessage.includes('sick')) {
      return 'symptoms';
    }
    return 'default';
  },

  // ...existing methods...
};
