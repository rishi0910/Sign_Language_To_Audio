require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');
const bcryptjs = require('bcryptjs');
const jwt = require('jsonwebtoken');
const session = require('express-session');
const passport = require('passport');
const LocalStrategy = require('passport-local').Strategy;
const GoogleStrategy = require('passport-google-oauth20').Strategy;

const app = express();

// Middleware
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS || 'http://localhost:5000',
  credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(__dirname));

// Session configuration
app.use(session({
  secret: process.env.SESSION_SECRET || 'your-secret-key-change-this',
  resave: false,
  saveUninitialized: true,
  cookie: { 
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Passport middleware
app.use(passport.initialize());
app.use(passport.session());

const dns = require('dns');
if (dns.setDefaultResultOrder) {
  dns.setDefaultResultOrder('ipv4first');
}

// MongoDB Connection
const uri = process.env.MONGODB_URI;
mongoose.connect(uri)
  .then(() => console.log("✅ Successfully connected to MongoDB Atlas!"))
  .catch((err) => console.error("❌ MongoDB connection error:", err));

// ==========================================
// MONGODB SCHEMA & MODELS
// ==========================================

// Enhanced User Schema with password hashing
const userSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    lowercase: true,
    index: true
  },
  password: {
    type: String,
    default: null // null for Google OAuth users
  },
  googleId: {
    type: String,
    default: null,
    sparse: true,
    index: true
  },
  displayName: {
    type: String,
    default: ''
  },
  authMethod: {
    type: String,
    enum: ['email-password', 'google'],
    required: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  },
  isEmailVerified: {
    type: Boolean,
    default: false
  }
});

// Hash password before saving
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) {
    return next();
  }
  
  if (this.password) {
    try {
      const salt = await bcryptjs.genSalt(10);
      this.password = await bcryptjs.hash(this.password, salt);
      next();
    } catch (error) {
      next(error);
    }
  } else {
    next();
  }
});

// Method to compare passwords
userSchema.methods.comparePassword = async function(enteredPassword) {
  return await bcryptjs.compare(enteredPassword, this.password);
};

const User = mongoose.model('User', userSchema);

// Keep old Account model for compatibility
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

// ==========================================
// PASSPORT STRATEGIES
// ==========================================

// Local Strategy for Email/Password
passport.use(new LocalStrategy({
  usernameField: 'email',
  passwordField: 'password'
}, async (email, password, done) => {
  try {
    const user = await User.findOne({ email: email.toLowerCase() });
    if (!user) {
      return done(null, false, { message: 'User not found' });
    }
    
    if (user.authMethod === 'google') {
      return done(null, false, { message: 'Please sign in with Google' });
    }
    
    const isPasswordValid = await user.comparePassword(password);
    if (!isPasswordValid) {
      return done(null, false, { message: 'Invalid password' });
    }
    
    return done(null, user);
  } catch (error) {
    return done(error);
  }
}));

// Google Strategy
passport.use(new GoogleStrategy({
    clientID: process.env.GOOGLE_CLIENT_ID || 'placeholder-client-id',
    clientSecret: process.env.GOOGLE_CLIENT_SECRET || 'placeholder-client-secret',
    callbackURL: process.env.GOOGLE_CALLBACK_URL || 'http://localhost:5000/api/auth/google/callback'
  }, async (accessToken, refreshToken, profile, done) => {
    try {
      let user = await User.findOne({ googleId: profile.id });
      
      if (user) {
        return done(null, user);
      }
      
      // Check if email exists (from email-password signup)
      user = await User.findOne({ email: profile.emails[0].value.toLowerCase() });
      
      if (user && user.authMethod === 'email-password') {
        // Link Google account to existing email
        user.googleId = profile.id;
        user.displayName = profile.displayName;
        await user.save();
        return done(null, user);
      }
      
      // Create new user
      user = new User({
        email: profile.emails[0].value.toLowerCase(),
        googleId: profile.id,
        displayName: profile.displayName,
        authMethod: 'google',
        isEmailVerified: true
      });
      
      await user.save();
      return done(null, user);
    } catch (error) {
      return done(error);
    }
  }
));

// Serialize user for session
passport.serializeUser((user, done) => {
  done(null, user.id);
});

// Deserialize user from session
passport.deserializeUser(async (id, done) => {
  try {
    const user = await User.findById(id);
    done(null, user);
  } catch (error) {
    done(error);
  }
});

// ==========================================
// MIDDLEWARE
// ==========================================

// JWT verification middleware
const verifyJWT = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1] || req.cookies?.authToken;
  
  if (!token) {
    return res.status(401).json({ message: 'No token provided' });
  }
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-jwt-secret-change-this');
    req.userId = decoded.userId;
    next();
  } catch (error) {
    return res.status(401).json({ message: 'Invalid or expired token' });
  }
};

// ==========================================
// API ROUTES
// ==========================================

// AUTH ROUTES

// Register with email and password
app.post('/api/auth/register', async (req, res) => {
  try {
    const { email, password, confirmPassword, displayName } = req.body;
    
    // Validation
    if (!email || !password || !confirmPassword) {
      return res.status(400).json({ 
        success: false, 
        message: 'Email and password are required' 
      });
    }
    
    if (password !== confirmPassword) {
      return res.status(400).json({ 
        success: false, 
        message: 'Passwords do not match' 
      });
    }
    
    if (password.length < 6) {
      return res.status(400).json({ 
        success: false, 
        message: 'Password must be at least 6 characters' 
      });
    }
    
    // Check if user exists
    const existingUser = await User.findOne({ email: email.toLowerCase() });
    if (existingUser) {
      return res.status(409).json({ 
        success: false, 
        message: 'Email already registered' 
      });
    }
    
    // Create new user
    const user = new User({
      email: email.toLowerCase(),
      password: password,
      displayName: displayName || email.split('@')[0],
      authMethod: 'email-password'
    });
    
    await user.save();
    
    // Generate JWT token
    const token = jwt.sign(
      { userId: user._id, email: user.email },
      process.env.JWT_SECRET || 'your-jwt-secret-change-this',
      { expiresIn: '24h' }
    );
    
    res.status(201).json({
      success: true,
      message: 'Account created successfully',
      token: token,
      user: {
        id: user._id,
        email: user.email,
        displayName: user.displayName
      }
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Registration failed',
      error: error.message 
    });
  }
});

// Login with email and password
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ 
        success: false, 
        message: 'Email and password are required' 
      });
    }
    
    const user = await User.findOne({ email: email.toLowerCase() });
    
    if (!user) {
      return res.status(401).json({ 
        success: false, 
        message: 'Invalid email or password' 
      });
    }
    
    if (user.authMethod === 'google') {
      return res.status(400).json({ 
        success: false, 
        message: 'Please sign in with Google' 
      });
    }
    
    const isPasswordValid = await user.comparePassword(password);
    if (!isPasswordValid) {
      return res.status(401).json({ 
        success: false, 
        message: 'Invalid email or password' 
      });
    }
    
    // Generate JWT token
    const token = jwt.sign(
      { userId: user._id, email: user.email },
      process.env.JWT_SECRET || 'your-jwt-secret-change-this',
      { expiresIn: '24h' }
    );
    
    res.json({
      success: true,
      message: 'Login successful',
      token: token,
      user: {
        id: user._id,
        email: user.email,
        displayName: user.displayName
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Login failed',
      error: error.message 
    });
  }
});

// Google OAuth routes
app.get('/api/auth/google',
  passport.authenticate('google', { scope: ['profile', 'email'] })
);

app.get('/api/auth/google/callback',
  passport.authenticate('google', { failureRedirect: '/#login' }),
  async (req, res) => {
    try {
      // Generate JWT token for authenticated user
      const token = jwt.sign(
        { userId: req.user._id, email: req.user.email },
        process.env.JWT_SECRET || 'your-jwt-secret-change-this',
        { expiresIn: '24h' }
      );
      
      // Redirect to frontend with token in hash (or query for better practice)
      res.redirect(`/#/profile?token=${token}&email=${req.user.email}&name=${req.user.displayName}`);
    } catch (error) {
      res.redirect('/#login?error=auth-failed');
    }
  }
);

// Get current user
app.get('/api/auth/me', verifyJWT, async (req, res) => {
  try {
    const user = await User.findById(req.userId).select('-password');
    if (!user) {
      return res.status(404).json({ 
        success: false, 
        message: 'User not found' 
      });
    }
    
    res.json({
      success: true,
      user: {
        id: user._id,
        email: user.email,
        displayName: user.displayName,
        authMethod: user.authMethod
      }
    });
  } catch (error) {
    res.status(500).json({ 
      success: false, 
      message: 'Failed to fetch user',
      error: error.message 
    });
  }
});

// Logout (frontend will clear token)
app.post('/api/auth/logout', (req, res) => {
  res.json({
    success: true,
    message: 'Logged out successfully'
  });
});

// Check if email exists
app.post('/api/auth/check-email', async (req, res) => {
  try {
    const { email } = req.body;
    
    if (!email) {
      return res.status(400).json({ 
        success: false, 
        message: 'Email is required' 
      });
    }
    
    const user = await User.findOne({ email: email.toLowerCase() });
    
    res.json({
      success: true,
      exists: !!user,
      authMethod: user?.authMethod || null
    });
  } catch (error) {
    res.status(500).json({ 
      success: false, 
      message: 'Error checking email',
      error: error.message 
    });
  }
});

// Get all users (for compatibility with old code)
app.get('/api/auth/accounts', async (req, res) => {
  try {
    const accounts = await User.find().sort({ createdAt: -1 }).select('email');
    const emails = accounts.map(acc => acc.email);
    res.json(emails);
  } catch (error) {
    res.status(500).json({ message: "Failed to fetch accounts", error: error.message });
  }
});

// Save account (for compatibility with old code)
app.post('/api/auth/save-account', async (req, res) => {
  try {
    const { email } = req.body;
    if (!email) {
      return res.status(400).json({ message: "Email is required" });
    }

    const existingUser = await User.findOne({ email: email.toLowerCase() });
    if (existingUser) {
      return res.status(200).json({ message: "Account already exists", success: true });
    }

    // Create user without password for demo
    const newUser = new User({ 
      email: email.toLowerCase(),
      authMethod: 'demo'
    });
    await newUser.save();
    
    res.status(201).json({ message: "Account saved successfully", success: true });
  } catch (error) {
    res.status(500).json({ message: "Failed to save account", error: error.message });
  }
});



// Start Server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚀 Backend Server running at: http://localhost:${PORT}`);
});
