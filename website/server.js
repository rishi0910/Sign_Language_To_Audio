require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
// Serve static frontend files from this directory
app.use(express.static(__dirname)); 

const dns = require('dns');
if (dns.setDefaultResultOrder) {
  dns.setDefaultResultOrder('ipv4first');
}

// MongoDB Connection
const uri = process.env.MONGODB_URI;
let dbConnected = false;
const mockDbPath = path.join(__dirname, 'mock-db.json');
let inMemoryEmails = [];
try {
  if (fs.existsSync(mockDbPath)) {
    inMemoryEmails = JSON.parse(fs.readFileSync(mockDbPath, 'utf8'));
  } else {
    inMemoryEmails = ["demo.user@college.edu", "test.student@gmail.com"];
    fs.writeFileSync(mockDbPath, JSON.stringify(inMemoryEmails));
  }
} catch(e) {
  inMemoryEmails = ["demo.user@college.edu", "test.student@gmail.com"];
}

mongoose.connect(uri, { serverSelectionTimeoutMS: 3000 })
  .then(() => {
    console.log("✅ Successfully connected to MongoDB Atlas!");
    dbConnected = true;
  })
  .catch((err) => {
    console.log("⚠️ CAUTION: Network is blocking MongoDB. Server is now running in 🚀 OFFLINE PRESENTATION MODE! Emails will just save to temporary memory.");
  });

// MongoDB Schema & Model for User Accounts
const accountSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    lowercase: true
  },
  addedAt: {
    type: Date,
    default: Date.now
  }
});
const Account = mongoose.model('Account', accountSchema);

const translationSchema = new mongoose.Schema({
  email: { type: String, required: true, lowercase: true },
  signText: { type: String, required: true },
  date: { type: Date, default: Date.now }
});
const Translation = mongoose.model('Translation', translationSchema);

const feedbackSchema = new mongoose.Schema({
  email: { type: String, lowercase: true },
  message: { type: String, required: true },
  date: { type: Date, default: Date.now }
});
const Feedback = mongoose.model('Feedback', feedbackSchema);

let inMemoryTranslations = [];
let inMemoryFeedbacks = [];
// ==========================================
// API ROUTES
// ==========================================

// Route: Get all saved accounts
app.get('/api/auth/accounts', async (req, res) => {
  try {
    if (!dbConnected) {
      // Fallback mode for presentation
      return res.json(inMemoryEmails);
    }
    const accounts = await Account.find().sort({ addedAt: -1 });
    // Extract just the emails into a simple array for the frontend
    const emails = accounts.map(acc => acc.email);
    res.json(emails);
  } catch (error) {
    res.status(500).json({ message: "Failed to fetch accounts", error: error.message });
  }
});

// Route: Save a newly added account
app.post('/api/auth/save-account', async (req, res) => {
  try {
    const { email } = req.body;
    if (!email) {
      return res.status(400).json({ message: "Email is required" });
    }

    if (!dbConnected) {
      // Fallback mode for presentation
      const lowerEmail = email.toLowerCase();
      if (!inMemoryEmails.includes(lowerEmail)) {
        inMemoryEmails.unshift(lowerEmail); // Add new email to the top
        try { fs.writeFileSync(mockDbPath, JSON.stringify(inMemoryEmails)); } catch(e){} // Persist
      }
      return res.status(201).json({ message: "Account saved locally for demo", success: true });
    }

    // Check if account already exists
    const existingAccount = await Account.findOne({ email });
    if (existingAccount) {
      return res.status(200).json({ message: "Account already exists", success: true });
    }

    // Save new account
    const newAccount = new Account({ email });
    await newAccount.save();
    
    res.status(201).json({ message: "Account saved successfully", success: true });
  } catch (error) {
    res.status(500).json({ message: "Failed to save account", error: error.message });
  }
});

// Route: Save a translation
app.post('/api/translations', async (req, res) => {
  try {
    const { email, signText } = req.body;
    if (!email || !signText) return res.status(400).json({ message: "Email and signText required" });
    if (!dbConnected) {
      inMemoryTranslations.unshift({ email: email.toLowerCase(), signText, date: new Date() });
      return res.status(201).json({ message: "Saved offline", success: true });
    }
    const newTrans = new Translation({ email, signText });
    await newTrans.save();
    res.status(201).json({ message: "Translation saved", success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Route: Get translations for user
app.get('/api/translations/:email', async (req, res) => {
  try {
    const email = req.params.email.toLowerCase();
    if (!dbConnected) {
      const userTrans = inMemoryTranslations.filter(t => t.email === email);
      return res.json(userTrans);
    }
    const userTrans = await Translation.find({ email }).sort({ date: -1 }).limit(10);
    res.json(userTrans);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Route: Save feedback
app.post('/api/feedback', async (req, res) => {
  try {
    const { email, message } = req.body;
    if (!message) return res.status(400).json({ message: "Message is required" });
    if (!dbConnected) {
      inMemoryFeedbacks.unshift({ email, message, date: new Date() });
      return res.status(201).json({ message: "Feedback saved offline", success: true });
    }
    const newFeedback = new Feedback({ email, message });
    await newFeedback.save();
    res.status(201).json({ message: "Feedback saved", success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});


// Start Server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚀 Backend Server running at: http://localhost:${PORT}`);
});
