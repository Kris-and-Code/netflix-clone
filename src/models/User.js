const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true,
    unique: true
  },
  password: {
    type: String,
    required: true
  },
  profileName: {
    type: String,
    required: true
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
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('User', userSchema); 