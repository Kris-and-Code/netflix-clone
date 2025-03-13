const mongoose = require('mongoose');

const watchHistorySchema = new mongoose.Schema({
  content: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Content'
  },
  progress: Number,
  watchedAt: Date
});

const userSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true
  },
  password: {
    type: String,
    required: true
  },
  profileName: {
    type: String,
    required: true,
    trim: true
  },
  subscription: {
    type: String,
    enum: ['basic', 'standard', 'premium'],
    default: 'basic'
  },
  myList: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Content'
  }],
  watchHistory: [watchHistorySchema],
  preferences: {
    language: {
      type: String,
      default: 'en'
    },
    maturityLevel: {
      type: String,
      enum: ['kids', 'teen', 'adult'],
      default: 'adult'
    }
  },
  isActive: {
    type: Boolean,
    default: true
  },
  lastLogin: Date,
  createdAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Add index for email
userSchema.index({ email: 1 });

module.exports = mongoose.model('User', userSchema); 